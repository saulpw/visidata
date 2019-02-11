#!/bin/bash

aws=${aws:-echo aws}

cd plugins
for p in `find . -type d` ; do ( cd $p && zip -r $p.zip . ) ; done
cd ..

$aws s3 cp --profile saulpw --acl public-read plugins/plugins.tsv s3://visidata.org/plugins/
$aws s3 cp --profile saulpw --acl public-read plugins/*.zip s3://visidata.org/plugins/
