#!/bin/zsh

# Stops the execution of a script if there is an error
set -x
set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$BUILD/www
DEMO=$VD/www/tour
MAN=$VD/docs/man

mkdir -p $WWW/man
mkdir -p $WWW/tour

$VD/build.sh

echo '<section><pre>' > $BUILD/vd-man-inc.html
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
$VD/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $VD/www/template.html > $WWW/man/index.html

### build front page from README

$VD/strformat.py body=$VD/www/frontpage-body.html title="VisiData" head='' < $VD/www/template.html > $WWW/index.html
#markdown $VD/README.md > $WWW/index.html
#

# Builds tours
$DEMO/mkindex.py $DEMO/*.yaml > $BUILD/demo-index-body.html
# Which main css file is it referencing?
$VD/strformat.py body=$BUILD/demo-index-body.html title="Tour Index" head='' < $VD/www/template.html > $WWW/tour/index.html

for tpath in `find $DEMO -name '*.yaml'`; do
    tyaml=${tpath##$DEMO/}
    tfolder=${tyaml%.yaml}
    mkdir -p $WWW/tour/$tfolder
    $VD/strformat.py body=<($DEMO/mkdemo.py $DEMO/$tyaml) title="VisiData tour: $tfolder" head=$DEMO/demo-head-inc.html < $VD/www/template.html > $WWW/tour/$tfolder/index.html

    cp $VD/www/*.* $WWW
    cp $DEMO/$tfolder/*.* $WWW/tour/$tfolder
    cp $DEMO/asciinema-player.* $WWW/tour
    cp $DEMO/*.css $WWW/tour
done

#### At the end
# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/docs/analytics.thtml" -e 'd}' $fn
done

