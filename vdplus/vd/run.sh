#!/bin/sh

CMD_LOG=/var/log/visidata_commands.log
GOTTY_PORT=${GOTTY_PORT:-9000}

# Start an HTTP server that exposes VisiData's TTY in the browser
/app/bin/gotty -w -p $GOTTY_PORT vd /app/data &

# The odd location of this line is because for some strange reason `touch`ing the
# the $CMD_LOG file causes VisiData to log blank lines??
while ! ls $CMD_LOG > /dev/null 2>&1; do sleep 0.1; done

# Add the command history to the container's output
parallel --tagstring "VDCMD:" --line-buffer tail -f {} ::: $CMD_LOG
