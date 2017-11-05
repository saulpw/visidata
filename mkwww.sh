#!/bin/zsh

# Stop the execution of a script if there is an error
set -x
set -e

# Set up variables
VD=~/git/visidata
BUILD=$VD/_build
BUILDWWW=$BUILD/www
MAN=$VD/visidata/man
TEST=$VD/www/test
DESIGN=$VD/www/design

# Build directories
mkdir -p $BUILD
mkdir -p $BUILDWWW
mkdir -p $BUILDWWW/man
mkdir -p $BUILDWWW/test
mkdir -p $BUILDWWW/design

# Set up python and shell environment
export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH

### Build manpage
cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -rt -I $BUILD $BUILD/vd-skel.1 > $BUILD/vd-pre.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1   # checked in

# build front page of visidata.org
$VD/strformat.py body=$VD/www/frontpage-body.html title="VisiData" head='' < $VD/www/template.html > $BUILDWWW/index.html

# Build /man
echo '<section><pre>' > $BUILD/vd-man-inc.html
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
$VD/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $VD/www/template.html > $BUILDWWW/man/index.html

# Build /tests
$TEST/mkindex.py $TEST/*.yaml > $BUILD/test-index-body.html
$VD/strformat.py body=$BUILD/test-index-body.html title="test Index" head='' < $VD/www/template.html > $BUILDWWW/test/index.html
for tpath in `find $TEST -name '*.yaml'`; do
    tyaml=${tpath##$TEST/}
    tfolder=${tyaml%.yaml}
    mkdir -p $BUILDWWW/test/$tfolder
    $VD/strformat.py body=<($TEST/mkdemo.py $TEST/$tyaml) title="VisiData test: $tfolder" head=$TEST/test-head-inc.html < $VD/www/template.html > $BUILDWWW/test/$tfolder/index.html
# Rewrite this so I am only copying over the relevant html and css
    cp $VD/www/*.* $BUILDWWW
    cp $TEST/$tfolder/*.* $BUILDWWW/test/$tfolder
    cp $TEST/asciinema-player.* $BUILDWWW/test
    cp $TEST/*.css $BUILDWWW/test
done

# Build /design
pandoc -r markdown -w html -o $BUILDWWW/design/index.body $VD/www/design.md
$VD/strformat.py body=$BUILDWWW/design/index.body title="VisiData Design and Internals" head="" < $VD/www/template.html > $BUILDWWW/design/index.html
for postpath in `find $DESIGN -name '*.md'`; do
    post=${postpath##$DESIGN/}
    postname=${post%.md}
    mkdir -p $BUILDWWW/design/$postname
    posthtml=$BUILDWWW/design/$postname/index
    pandoc -r markdown -w html -o $posthtml.body $postpath
    $VD/strformat.py body=$posthtml.body title=$postname head="" < $VD/www/template.html > $posthtml.html
done

# Build /news

# Build /help

#### At the end
# add analytics to .html files
for fn in `find $BUILDWWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/www/analytics.thtml" -e 'd}' $fn
done

# Cleanup files in _build which we do not need to upload
#
