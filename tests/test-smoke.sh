#!/usr/bin/env bash
# Ensure VisiData starts and can open a directory
source tests/testenv.sh
$VD --version
$VD -f dir . --batch -o /dev/null
