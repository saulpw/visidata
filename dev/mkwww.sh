#!/bin/zsh

# Stop the execution of a script if there is an error
set -e

# Set up variables
VD=~/git/visidata
DEV=$VD/dev
WWW=$VD/www
BUILD=$VD/_build
BUILDWWW=$BUILD/www
MAN=$VD/visidata/man
DOCS=$WWW/docs
HOWTODEV=$WWW/howto/dev
NEWS=$WWW/news
VIDEOS=$WWW/videos
HELP=$WWW/help
INSTALL=$WWW/install

# Build directories
mkdir -p $BUILD
mkdir -p $BUILDWWW
mkdir -p $BUILDWWW/man
mkdir -p $BUILDWWW/docs
mkdir -p $BUILDWWW/howto/dev
mkdir -p $BUILDWWW/about
mkdir -p $BUILDWWW/contributing
mkdir -p $BUILDWWW/help
mkdir -p $BUILDWWW/install
mkdir -p $BUILDWWW/videos

# Set up python and shell environment
export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH

### Build manpage
cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -rt -I $BUILD $BUILD/vd.inc > $BUILD/vd-pre.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1   # checked in

# build front page of visidata.org
$DEV/strformat.py body=$WWW/frontpage-body.html title="VisiData" head='' < $WWW/template.html > $BUILDWWW/index.html
for i in 404.html robots.txt main.css ; do
    cp $WWW/$i $BUILDWWW/
done

# Build /about
pandoc -r markdown -w html -o $BUILDWWW/about/index.body $WWW/about.md
$DEV/strformat.py body=$BUILDWWW/about/index.body title="About VisiData" head="" < $WWW/template.html > $BUILDWWW/about/index.html

# Build /man
echo '<section><pre id="manpage">' > $BUILD/vd-man-inc.html
# <pre> max-width in main.css should be half of COLUMNS=###
MAN_KEEP_FORMATTING=1 COLUMNS=120 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
#  Properties of columns on the source sheet can be changed with standard editing commands (e
$DEV/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $WWW/template.html > $BUILDWWW/man/index.html

# Create http://visidata.org/man/#loaders
sed -i -e "s#<span style=\"font-weight:bold;\">SUPPORTED</span> <span style=\"font-weight:bold;\">SOURCES</span>#<span style=\"font-weight-:bold;\"><a name=\"loaders\">SUPPORTED SOURCES</a></span>#g" $BUILDWWW/man/index.html

# Build /contributing
pandoc -r markdown -w html -o $BUILDWWW/contributing/index.body $VD/CONTRIBUTING.md
$DEV/strformat.py body=$BUILDWWW/contributing/index.body title="Contributing to VisiData" head="" < $WWW/template.html > $BUILDWWW/contributing/index.html

# Build /help
pandoc -r markdown -w html -o $BUILDWWW/help/index.body $HELP/index.md
$DEV/strformat.py body=$BUILDWWW/help/index.body title="Support" head="" < $WWW/template.html > $BUILDWWW/help/index.html

# Build /install
pandoc -r markdown -w html -o $BUILDWWW/install/index.body $INSTALL/index.md
$DEV/strformat.py body=$BUILDWWW/install/index.body title="Installation" head="" < $WWW/template.html > $BUILDWWW/install/index.html

# Create http://visidata.org/install/#pip3
sed -i -e "s#<h2 id=\"install-via-pip3\">Install via pip3</h2>#<h2 id=\"install-via-pip3\"><a name=\"pip3\">Install via pip3</a></h2>#g" $BUILDWWW/install/index.html
# Create http://visidata.org/install/#brew
sed -i -e "s#<h2 id=\"install-via-brew\">Install via brew</h2>#<h2 id=\"install-via-brew\"><a name=\"brew\">Install via brew</a></h2>#g" $BUILDWWW/install/index.html
# Create http://visidata.org/install/#apt
sed -i -e "s#<h2 id=\"install-via-apt\">Install via apt</h2>#<h2 id=\"install-via-apt\"><a name=\"apt\">Install via apt</a></h2>#g" $BUILDWWW/install/index.html

# Build /videos
$DEV/strformat.py body=$VIDEOS/video-body.html title="VisiData Videos" head="" < $WWW/template.html > $BUILDWWW/videos/index.html

# build /docs index
pandoc -r markdown -w html -o $BUILDWWW/docs/index.body $WWW/docs.md
$DEV/strformat.py body=$BUILDWWW/docs/index.body title="VisiData documentation" head="" < $WWW/template.html > $BUILDWWW/docs/index.html
rm -f $BUILDWWW/docs/index.body

# Build /docs/*
for postpath in `find $DOCS -name '*.md'`; do
    post=${postpath##$DOCS/}
    postname=${post%.md}
    mkdir -p $BUILDWWW/docs/$postname
    posthtml=$BUILDWWW/docs/$postname/index
    pandoc -r markdown -w html -o $posthtml.body $postpath
    $DEV/strformat.py body=$posthtml.body title=$postname head="" < $WWW/template.html > $posthtml.html
    rm -f $posthtml.body
done

# Build /howto/dev
for postpath in `find $HOWTODEV -name '*.md'`; do
    post=${postpath##$HOWTODEV/}
    postname=${post%.md}
    mkdir -p $BUILDWWW/howto/dev/$postname
    posthtml=$BUILDWWW/howto/dev/$postname/index
    pandoc -r markdown -w html -o $posthtml.body $postpath
    $DEV/strformat.py body=$posthtml.body title=$postname head="" < $WWW/template.html > $posthtml.html
    rm -f $posthtml.body
done

# Build /news
mkdir -p $BUILDWWW/news
$NEWS/mknews.py $NEWS/news.tsv > $BUILD/news.body
$DEV/strformat.py body=$BUILD/news.body title="VisiData News" head='' < $WWW/template.html > $BUILDWWW/news/index.html

for postpath in `find $NEWS -name '*.md'`; do
    post=${postpath##$NEWS/}
    postname=${post%.md}
    mkdir -p $BUILDWWW/news/$postname
    posthtml=$BUILDWWW/news/$postname/index
    pandoc -r markdown -w html -o $posthtml.body $postpath
    $DEV/strformat.py body=$posthtml.body title=$postname head="" < $WWW/template.html > $posthtml.html
    rm -f $posthtml.body
done

# Add the key
cp $WWW/devotees.gpg.key $BUILDWWW

#### At the end
# add analytics to .html files
for fn in `find $BUILDWWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/www/analytics.thtml" -e 'd}' $fn
done

