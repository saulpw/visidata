#!/bin/sh

# Stops the execution of a script if there is an error
set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$BUILD/www
DEMO=$VD/www/demo
MAN=$VD/docs/man

mkdir -p $WWW/man/vd
mkdir -p $WWW/demo

MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha > $WWW/man/vd/index.html

### build front page from README

markdown $VD/README.md > $WWW/index.html

# Builds tours
for tpath in `find $DEMO -name '*.yaml'`; do
    tname=${tpath##$DEMO/}
    tfolder=${tname%.yaml}
    $DEMO/mkdemo.py $DEMO/demo.thtml $DEMO/$tname > $DEMO/$tfolder/index.html
    mkdir -p $WWW/demo/$tfolder
    cp $DEMO/$tfolder/* $WWW/demo/$tfolder
    cp $DEMO/asciinema-player.* $WWW/demo
done

#### At the end
# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/docs/analytics.thtml" -e 'd}' $fn
done

