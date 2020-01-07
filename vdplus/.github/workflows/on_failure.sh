#!/usr/bin/env bash

cat vdhub.logs
cat vdwww.logs

screenshot=$(find hub/test/screenshots -name '*.png' -print -quit | xargs)
curl \
  --location \
  --request POST \
  "https://api.imgbb.com/1/upload?key=14441c5834c2b4f14b63865bf52cf77c" \
  -F "image=@$screenshot"

