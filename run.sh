#!/bin/sh

exec xvfb-run -a "--server-args=-screen 0, 1024x1024x24" python server.py --aspect-ratio=crop $*

