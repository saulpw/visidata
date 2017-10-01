#!/bin/zsh

# Stops the execution of a script if there is an error
set -x
set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$BUILD/www
DEMO=$VD/www/demo
MAN=$VD/docs/man

mkdir -p $WWW/man/vd
mkdir -p $WWW/demo

$VD/build.sh

MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha --no-header > $BUILD/vd-man-inc.html
$VD/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $VD/www/template.html > $WWW/man/vd/index.html

### build front page from README

markdown $VD/README.md > $WWW/index.html

# Builds tours
$DEMO/mkindex.py $DEMO/*.yaml > $BUILD/demo-index-body.html
# Which main css file is it referencing?
$VD/strformat.py body=$BUILD/demo-index-body.html title="Tutorials Index" head='' < $VD/www/template.html > $WWW/demo/index.html

for tpath in `find $DEMO -name 'pivot.yaml'`; do
    tyaml=${tpath##$DEMO/}
    tfolder=${tyaml%.yaml}
    mkdir -p $WWW/demo/$tfolder
    $VD/strformat.py body=<($DEMO/mkdemo.py $DEMO/$tyaml) title="VisiData tutorial: $tfolder" head=$DEMO/demo-head-inc.html < $VD/www/template.html > $WWW/demo/$tfolder/index.html

    cp $VD/www/* $WWW
    cp $DEMO/$tfolder/* $WWW/demo/$tfolder
    cp $DEMO/asciinema-player.* $WWW/demo
    cp $DEMO/*.css $WWW/demo
done

#### At the end
# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/docs/analytics.thtml" -e 'd}' $fn
done

