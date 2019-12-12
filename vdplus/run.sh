#!/bin/sh

CMD_LOG=/var/log/visidata_commands.log

# Start an HTTP server that exposes VisiData's TTY in the browser
/app/bin/gotty -w -p 9000 vd /app/data &

# The odd location of this line is because for some strange reason `touch`ing the
# the $CMD_LOG file causes VisiData to log blank lines??
while ! ls $CMD_LOG > /dev/null 2>&1; do sleep 0.1; done

# Add the command history to the container's output
tail -f $CMD_LOG | xargs -I{} echo "VDCMD: {}"
