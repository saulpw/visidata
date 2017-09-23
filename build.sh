#!/bin/sh

set -e

VD=~/git/visidata
BUILD=$VD/_build
WWW=$VD/_build/www
MAN=$VD/docs/man

mkdir -p $WWW/man/vd

export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH

### build manpage

cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -I $BUILD $BUILD/vd-skel.1 > $BUILD/vd-pre.1
preconv -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1   # checked in
gzip -c $MAN/vd.1 > $BUILD/vd.1.gz
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MAN/vd.1 | ul | aha > $WWW/man/vd/index.html

### build front page from README

markdown $VD/README.md > $WWW/index.html

# add analytics to .html files
for fn in `find $WWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/docs/analytics.thtml" -e 'd}' $fn
done


