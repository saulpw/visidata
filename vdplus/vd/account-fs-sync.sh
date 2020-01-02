#!/bin/bash

BASE_ACCOUNT_PATH=${BASE_ACCOUNT_PATH:-/app/account/}
export SOURCE=$BASE_ACCOUNT_PATH
export USER_ACCOUNT="s3://vdata/accounts/$USER_ID/"

function s3() {
  s3cmd \
    --host sfo2.digitaloceanspaces.com \
    --host-bucket '%(bucket).sfo2.digitaloceanspaces.com' \
    --access_key $DO_SPACES_API_ID \
    --secret_key $DO_SPACES_API_SECRET \
    "$@"
}
export -f s3

# First download the current account FS from DO Spaces
echo "Attempting to download user account ($USER_ID) from DO Spaces..."
s3 sync $USER_ACCOUNT $SOURCE

# It's very important that we exit here, because if we start syncing an empty
# or half-downloaded folder then files will get deleted on DO!
if [ $? -ne 0 ]; then
  touch $SOURCE"downloading_user_account_failed!"
  exit 1
fi

# Continuously sync forever
echo "Starting account folder sync daemon for user account ($USER_ID)..."
while :; do
  timeout 600 bash -c "s3 sync --delete-removed $SOURCE $USER_ACCOUNT"
  sleep 1
done
