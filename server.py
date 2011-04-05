#!/usr/bin/env python
#
# server.py
#
# Copyright (c) 2011 Shinya Kasatani
# Copyright (c) 2008 Roland Tapken <roland@dau-sicher.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import sys
import traceback
sys.path.append('webkit2png')
from webkit2png import *
from Queue import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import re

class ScreenshotRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        response_queue = Queue()
        m = re.match(r'/(?:(\d+)x(\d+)/)?(https?://.+)', self.path)
        if m:
            self.server.queue.put((m.group(3), 
                                   m.group(1) and int(m.group(1)), 
                                   m.group(2) and int(m.group(2)),
                                   response_queue))
            response = response_queue.get(True)
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_response(404, 'Not Found')

class ScreenshotServer(HTTPServer):
    def __init__(self, server_address, queue):
        HTTPServer.__init__(self, server_address, ScreenshotRequestHandler)
        self.queue = queue

class ServerThread(Thread):
    def __init__(self, queue, port = 10080):
        Thread.__init__(self)
        self.queue = queue
        self.port = port

    def run(self):
        try:
            server = ScreenshotServer(('', self.port), self.queue)
            server.serve_forever()
        except:
            traceback.print_exc()
            self.queue.put(None)

# Based on __main__ from webkit2png.py
if __name__ == '__main__':
    # This code will be executed if this module is run 'as-is'.

    # Enable HTTP proxy
    if 'http_proxy' in os.environ:
        proxy_url = urlparse.urlparse(os.environ.get('http_proxy'))
        proxy = QNetworkProxy(QNetworkProxy.HttpProxy, proxy_url.hostname, proxy_url.port)
        QNetworkProxy.setApplicationProxy(proxy)
    
    # Parse command line arguments.
    # Syntax:
    # $0 [--xvfb|--display=DISPLAY] [--debug] [--output=FILENAME] <URL>

    description = "Creates a screenshot of a website using QtWebkit." \
                + "This program comes with ABSOLUTELY NO WARRANTY. " \
                + "This is free software, and you are welcome to redistribute " \
                + "it under the terms of the GNU General Public License v2."

    parser = OptionParser(usage="usage: %prog [options] <URL>",
                          version="%prog " + VERSION + ", Copyright (c) Roland Tapken",
                          description=description, add_help_option=True)
    parser.add_option("-x", "--xvfb", nargs=2, type="int", dest="xvfb",
                      help="Start an 'xvfb' instance with the given desktop size.", metavar="WIDTH HEIGHT")
    parser.add_option("-g", "--geometry", dest="geometry", nargs=2, default=(0, 0), type="int",
                      help="Geometry of the virtual browser window (0 means 'autodetect') [default: %default].", metavar="WIDTH HEIGHT")
    #parser.add_option("-o", "--output", dest="output",
    #                  help="Write output to FILE instead of STDOUT.", metavar="FILE")
    parser.add_option("-f", "--format", dest="format", default="png",
                      help="Output image format [default: %default]", metavar="FORMAT")
    parser.add_option("--scale", dest="scale", nargs=2, type="int",
                      help="Scale the image to this size", metavar="WIDTH HEIGHT")
    parser.add_option("--aspect-ratio", dest="ratio", type="choice", choices=["ignore", "keep", "expand", "crop"],
                      help="One of 'ignore', 'keep', 'crop' or 'expand' [default: %default]")
    parser.add_option("-F", "--feature", dest="features", action="append", type="choice",
                      choices=["javascript", "plugins"],
                      help="Enable additional Webkit features ('javascript', 'plugins')", metavar="FEATURE")
    parser.add_option("-w", "--wait", dest="wait", default=0, type="int",
                      help="Time to wait after loading before the screenshot is taken [default: %default]", metavar="SECONDS")
    parser.add_option("-t", "--timeout", dest="timeout", default=0, type="int",
                      help="Time before the request will be canceled [default: %default]", metavar="SECONDS")
    parser.add_option("-W", "--window", dest="window", action="store_true",
                      help="Grab whole window instead of frame (may be required for plugins)", default=False)
    parser.add_option("-T", "--transparent", dest="transparent", action="store_true",
                      help="Render output on a transparent background (Be sure to have a transparent background defined in the html)", default=False)
    parser.add_option("", "--style", dest="style",
                      help="Change the Qt look and feel to STYLE (e.G. 'windows').", metavar="STYLE")
    parser.add_option("-d", "--display", dest="display",
                      help="Connect to X server at DISPLAY.", metavar="DISPLAY")
    parser.add_option("--debug", action="store_true", dest="debug",
                      help="Show debugging information.", default=False)
    parser.add_option("--log", action="store", dest="logfile", default=LOG_FILENAME,
                      help="Select the log output file",)
    parser.add_option("--pidfile", action="store", dest="pidfile",
                      help="Output PID to file",)
    parser.add_option("--port", dest="port", type="int", default=10080,
                      help="Server port number")

    # Parse command line arguments and validate them (as far as we can)
    (options,args) = parser.parse_args()
    #if len(args) != 1:
    #    parser.error("incorrect number of arguments")
    if options.display and options.xvfb:
        parser.error("options -x and -d are mutually exclusive")
    #options.url = args[0]

    logging.basicConfig(filename=options.logfile,level=logging.WARN,)

    # Enable output of debugging information
    if options.debug:
        logger.setLevel(logging.DEBUG)

    if options.pidfile:
        f = open(options.pidfile, 'w')
        f.write(str(os.getpid()))
        f.close()

    if options.xvfb:
        # Start 'xvfb' instance by replacing the current process
        server_num = int(os.getpid() + 1e6)
        newArgs = ["xvfb-run", "--auto-servernum", "--server-num", str(server_num), "--server-args=-screen 0, %dx%dx24" % options.xvfb, sys.argv[0]]
        skipArgs = 0
        for i in range(1, len(sys.argv)):
            if skipArgs > 0:
                skipArgs -= 1
            elif sys.argv[i] in ["-x", "--xvfb"]:
                skipArgs = 2 # following: width and height
            else:
                newArgs.append(sys.argv[i])
        logger.debug("Executing %s" % " ".join(newArgs))
        os.execvp(newArgs[0],newArgs[1:])
        
    logger.debug("Version %s, Python %s, Qt %s", VERSION, sys.version, qVersion());

    # Technically, this is a QtGui application, because QWebPage requires it
    # to be. But because we will have no user interaction, and rendering can
    # not start before 'app.exec_()' is called, we have to trigger our "main"
    # by a timer event.
    def __main_qt():
        # Render the page.
        # If this method times out or loading failed, a
        # RuntimeException is thrown
        try:
            # Initialize WebkitRenderer object
            renderer = WebkitRenderer()
            renderer.width = options.geometry[0]
            renderer.height = options.geometry[1]
            renderer.timeout = options.timeout
            renderer.wait = options.wait
            renderer.format = options.format
            renderer.grabWholeWindow = options.window
            renderer.renderTransparentBackground = options.transparent

            if options.ratio:
                renderer.scaleRatio = options.ratio
                
            if options.scale:
                renderer.scaleToWidth = options.scale[0]
                renderer.scaleToHeight = options.scale[1]

            if options.features:
                if "javascript" in options.features:
                    renderer.qWebSettings[QWebSettings.JavascriptEnabled] = True
                if "plugins" in options.features:
                    renderer.qWebSettings[QWebSettings.PluginsEnabled] = True

            request = Queue()
            thread = ServerThread(request, options.port)
            thread.start()
            
            while(True):
                r = request.get(True)
                if r:
                    url, width, height, response = r
                    if width and height:
                        renderer.scaleToWidth = width
                        renderer.scaleToHeight = height
                    response.put(renderer.render_to_bytes(url))
                else:
                    break

            QApplication.exit(1)
        except RuntimeError, e:
            logger.error("main: %s" % e)
            print >> sys.stderr, e
            QApplication.exit(1)

    # Initialize Qt-Application, but make this script
    # abortable via CTRL-C
    app = init_qtgui(display = options.display, style=options.style)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QTimer.singleShot(0, __main_qt)
    sys.exit(app.exec_())
