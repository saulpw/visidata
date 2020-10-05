#!/bin/bash

set -e # stop script on error

# SRC is already cloned visidata repo, with no modifications
SRC=$(pwd)
export PYTHONPATH="$SRC"

# BUILD is output directory (corresponding to webroot)
BUILD="$SRC"/_build
mkdir -p "$BUILD"

sphinx-build -b html "$SRC"/docs/api "$BUILD"
