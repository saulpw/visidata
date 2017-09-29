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

