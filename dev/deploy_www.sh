#!/bin/sh

BUILD="${BUILD:-_build/www}"
SITE="${SITE:-beta.visidata.org}"
PROFILE="${PROFILE:-default}"

aws s3 sync --acl public-read --profile $PROFILE $BUILD s3://$SITE

REDIR_URL='https://www.surveymonkey.com/r/8JBN8BM'
REDIR_PATH=survey
aws s3 cp --profile $PROFILE --acl public-read --website-redirect="$REDIR_URL" $0 s3://$SITE/"$REDIR_PATH"

aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*" --profile $PROFILE
