#!/bin/sh

VD_CMD=${VD_CMD:-'vd /app/data'}

clear

# Disable CTRL+C exit
trap '' 2

# Don't ket users drop to shell
while :
do
  $VD_CMD
done
