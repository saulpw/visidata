#!/bin/env bash

function s3sync {
  dest=$(ls /export | grep ^pvc)
  [ ! -n "$dest" ] && return 1
  echo "Attempting to sync with DO Spaces..."
  s3cmd \
    --host sfo2.digitaloceanspaces.com \
    --host-bucket '%(bucket).sfo2.digitaloceanspaces.com' \
    --access_key $DO_SPACES_API_ID \
    --secret_key $DO_SPACES_API_SECRET \
    sync s3://vdata/ /export/$dest/
  echo "Sync ran."
}
export -f s3sync

# Continuously sync forever
while :; do
  timeout 600 bash -c s3sync
  sleep 1
done &

/nfs-provisioner -provisioner=cluster.local/nfs-server-nfs-server-provisioner
