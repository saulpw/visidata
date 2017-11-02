#!/bin/zsh

# Stops the execution of a script if there is an error
set -x
set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$BUILD/www
TEST=$VD/www/test
MAN=$VD/visidata/man

mkdir -p $WWW/man
mkdir -p $WWW/test

$VD/build.sh

echo '<section><pre>' > $BUILD/vd-man-inc.html
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
$VD/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $VD/www/template.html > $WWW/man/index.html

### build front page from README

$VD/strformat.py body=$VD/www/frontpage-body.html title="VisiData" head='' < $VD/www/template.html > $WWW/index.html
#markdown $VD/README.md > $WWW/index.html
#

# Builds tests
$TEST/mkindex.py $TEST/*.yaml > $BUILD/test-index-body.html
# Which main css file is it referencing?
$VD/strformat.py body=$BUILD/test-index-body.html title="test Index" head='' < $VD/www/template.html > $WWW/test/index.html

for tpath in `find $TEST -name '*.yaml'`; do
    tyaml=${tpath##$TEST/}
    tfolder=${tyaml%.yaml}
    mkdir -p $WWW/test/$tfolder
    $VD/strformat.py body=<($TEST/mkdemo.py $TEST/$tyaml) title="VisiData test: $tfolder" head=$TEST/test-head-inc.html < $VD/www/template.html > $WWW/test/$tfolder/index.html

    cp $VD/www/*.* $WWW
    cp $TEST/$tfolder/*.* $WWW/test/$tfolder
    cp $TEST/asciinema-player.* $WWW/test
    cp $TEST/*.css $WWW/test
done

#### At the end
# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/www/analytics.thtml" -e 'd}' $fn
done

