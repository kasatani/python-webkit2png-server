#!/bin/sh

cd `dirname $0`

case "$1" in
  start)
    sh run.sh --pidfile=$HOME/.webkit2png-server.pid 2>&1 > $HOME/.webkit2png-server.log &
    ;;

  stop)
    kill `cat $HOME/.webkit2png-server.pid`
    ;;

  *)
    echo "Usage: $0 start/stop" 
    exit 1;;
esac
