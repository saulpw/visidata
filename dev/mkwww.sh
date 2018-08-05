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


# Build directories
mkdir -p $BUILD
mkdir -p $BUILDWWW
mkdir -p $BUILDWWW/man
mkdir -p $BUILDWWW/docs
mkdir -p $BUILDWWW/install
mkdir -p $BUILDWWW/about
mkdir -p $BUILDWWW/releases
mkdir -p $BUILDWWW/contributing
mkdir -p $BUILDWWW/support

# Set up python and shell environment
export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH


# make_subfolder () {
# }

### Build manpage
cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -rt -I $BUILD $BUILD/vd.inc > $BUILD/vd-pre.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1   # checked in

# build front page of visidata.org
for i in 404.html robots.txt main.css ; do
    cp $WWW/$i $BUILDWWW/
done

# Build /
pandoc -r markdown -w html -o $BUILDWWW/index.body $WWW/index.md
$DEV/strformat.py body=$BUILDWWW/index.body title="VisiData" head="" < $WWW/template.html > $BUILDWWW/index.html

function make_page () {
    # $1 -> name of page
    # $2 -> title of page
    pandoc -r markdown -w html -o $BUILDWWW/$1/index.body $WWW/$1.md
    $DEV/strformat.py body=$BUILDWWW/$1/index.body title=$2 head="" < $WWW/template.html > $BUILDWWW/$1/index.html
}

# Build /about
make_page "about" "About Visidata"

# Build /man
echo '<section><pre id="manpage">' > $BUILD/vd-man-inc.html
# <pre> max-width in main.css should be half of COLUMNS=###
MAN_KEEP_FORMATTING=1 COLUMNS=120 man $MAN/vd.1 | ul | aha --no-header >> $BUILD/vd-man-inc.html
echo '</pre></section>' >> $BUILD/vd-man-inc.html
#  Properties of columns on the source sheet can be changed with standard editing commands (e
$DEV/strformat.py body=$BUILD/vd-man-inc.html title="VisiData Quick Reference" head="" < $WWW/template.html > $BUILDWWW/man/index.html

# Create /man/#loaders
sed -i -e "s#<span style=\"font-weight:bold;\">SUPPORTED</span> <span style=\"font-weight:bold;\">SOURCES</span>#<span style=\"font-weight:bold;\"><a name=\"loaders\">SUPPORTED SOURCES</a></span>#g" $BUILDWWW/man/index.html
# Create /man#edit for editing commands
sed -i -e "s#<span style=\"font-weight:bold;\">Editing</span> <span style=\"font-weight:bold;\">Rows</span> <span style=\"font-weight:bold;\">and</span> <span style=\"font-weight:bold;\">Cells</span>#<span style=\"font-weight:bold;\"><a name=\"edit\">Editing Rows and Cells</a></span>#g" $BUILDWWW/man/index.html
# Create /man#options
sed -i -e "s#<span style=\"font-weight:bold;\">COMMANDLINE</span> <span style=\"font-weight:bold;\">OPTIONS</span>#<span style=\"font-weight:bold;\"><a name=\"options\">OPTIONS</a></span>#g" $BUILDWWW/man/index.html
# Create /man#columns for columns sheet
sed -i -e "s#<span style=\"font-weight:bold;\">Columns</span> <span style=\"font-weight:bold;\">Sheet</span> <span style=\"font-weight:bold;\">(Shift-C)</span>#<span style=\"font-weight:bold;\"><a name=\"columns\">Columns Sheet (Shift-C)</a></span>#g" $BUILDWWW/man/index.html

# Build /contributing
pandoc -r markdown -w html -o $BUILDWWW/contributing/index.body $VD/CONTRIBUTING.md
$DEV/strformat.py body=$BUILDWWW/contributing/index.body title="Contributing to VisiData" head="" < $WWW/template.html > $BUILDWWW/contributing/index.html

# Build /install
make_page "install" "Quick Install"

# Build /support
make_page "support" "Support for VisiData"

# build /docs index
make_page "docs" "VisiData documentation"
rm -f $BUILDWWW/docs/index.body

# Build /docs/*
for postpath in `find $DOCS -name '*.md'`; do
    post=${postpath##$DOCS/}
    postname=${post%.md}
    mkdir -p $BUILDWWW/docs/$postname
    posthtml=$BUILDWWW/docs/$postname/index
    pandoc --from markdown_strict+table_captions+simple_tables+fenced_code_blocks -w html -o $posthtml.body $postpath
    $DEV/strformat.py body=$posthtml.body title=$postname head="" < $WWW/template.html > $posthtml.html
    rm -f $posthtml.body
done
mkdir -p $BUILDWWW/docs/casts
cp $DOCS/casts/* $BUILDWWW/docs/casts
cp $WWW/asciinema-player.* $BUILDWWW

# Build /kblayout

mkdir -p $BUILDWWW/docs/kblayout
$DEV/mklayout.py $VD/visidata/commands.tsv > $BUILDWWW/docs/kblayout/index.html
cp $WWW/kblayout.css $BUILDWWW/docs/kblayout/

# Build /releases
make_page "releases" "Releases"
rm -f $BUILDWWW/releases/index.body

# Add other toplevel static files
for fn in devotees.gpg.key vdlogo.png screenshot.png ; do
    cp $WWW/$fn $BUILDWWW/
done

#### At the end
# add analytics to .html files
for fn in `find $BUILDWWW -name '*.html'` ; do
    sed -i -e "/<head>/I{r $VD/www/analytics.thtml" -e 'd}' $fn
done
