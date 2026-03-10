#!/usr/bin/env bash
# Ensure VisiData can generate zsh completions
source tests/testenv.sh
$PYTHON dev/zsh-completion.py /dev/null
