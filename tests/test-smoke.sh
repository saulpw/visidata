#!/usr/bin/env bash
# Ensure VisiData starts and can open a directory
source tests/testenv.sh
VERSION=$($VD --version)
$VD -f dir . --batch -o /dev/null
echo "$VERSION; 1 passed in $(elapsed)s"
