#!/bin/sh

BUILD="${BUILD:-_build/www}"
SITE="${SITE:-beta.visidata.org}"
PROFILE="${PROFILE:-default}"

aws s3 sync --delete --acl public-read --profile $PROFILE $BUILD s3://$SITE
