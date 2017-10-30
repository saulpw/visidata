#!/bin/zsh

# Stops the execution of a script if there is an error
set -x
set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$BUILD/www
TOUR=$VD/www/tour
MAN=$VD/visidata/man

mkdir -p $WWW/man
mkdir -p $WWW/tour

$VD/build.sh

echo '<section><pre>' > $BUILD/vd-man-inc.html
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
$VD/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $VD/www/template.html > $WWW/man/index.html

### Build front page
$VD/strformat.py body=$VD/www/frontpage-body.html title="VisiData" head='' < $VD/www/template.html > $WWW/index.html

### Build any .md in checked-in www/
for fn in $VD/www/**/*.md ; do
    outpath=${fn##$VD/www/}
    outbase=${outpath%.md}
    mkdir -p $WWW/$outbase
    outfn=$WWW/$outbase/index.html
    $VD/strformat.py body=<(markdown $fn) title="$fn" head='' < $VD/www/template.html > $outfn
done

### Build tours
$TOUR/mkindex.py $TOUR/*.yaml > $BUILD/demo-index-body.html
# Which main css file is it referencing?
$VD/strformat.py body=$BUILD/demo-index-body.html title="Tour Index" head='' < $VD/www/template.html > $WWW/tour/index.html

for tpath in `find $TOUR -name '*.yaml'`; do
    tyaml=${tpath##$TOUR/}
    tfolder=${tyaml%.yaml}
    mkdir -p $WWW/tour/$tfolder
    $VD/strformat.py body=<($TOUR/mkdemo.py $TOUR/$tyaml) title="VisiData tour: $tfolder" head=$TOUR/demo-head-inc.html < $VD/www/template.html > $WWW/tour/$tfolder/index.html

    cp $VD/www/*.* $WWW
    cp $TOUR/$tfolder/*.* $WWW/tour/$tfolder
    cp $TOUR/asciinema-player.* $WWW/tour
    cp $TOUR/*.css $WWW/tour
done

#### At the end
# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/www/analytics.thtml" -e 'd}' $fn
done

