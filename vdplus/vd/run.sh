#!/bin/sh

CMD_LOG=/app/log/visidata_commands.log
GOTTY_PORT=${GOTTY_PORT:-9000}
VD_CMD=${VD_CMD:-'vd'}
ACCOUNT_PATH=/app/data

if [ -d $ACCOUNT_PATH ]; then
  while [ ! -f $ACCOUNT_PATH/.visidatarc ]; do sleep 0.05; done
  # Prevent default visidatarc conflicting with user's visidatarc
  rm /app/.visidatarc
fi

# Tmux makes it simple to support reconnections
tmux new-session -d -s VisiData -n window1
if [ -d $ACCOUNT_PATH ]; then
  tmux send-keys -t VisiData:window1 "cd $ACCOUNT_PATH" Enter
fi
tmux send-keys -t VisiData:window1 "$VD_CMD" Enter

(
  # The existence of this odd line is because for some strange reason `touch`ing the
  # the $CMD_LOG file causes VisiData to log blank lines??
  while ! ls $CMD_LOG > /dev/null 2>&1; do sleep 0.1; done

  # Add the command history to the container's output
  parallel --tagstring "VDCMD:" --line-buffer tail -f {} ::: $CMD_LOG
) &

# Start an HTTP server that exposes VisiData's TTY in the browser
/app/bin/gotty -w -p $GOTTY_PORT tmux attach -t VisiData:window1 &

# Exit once `vd` exits
while pgrep vd > /dev/null; do sleep 0.1; done
