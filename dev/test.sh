#!/usr/bin/env bash
# Wrapper for tests/test-vdx.sh (cmdlog golden tests)
# Usage: test.sh [-d] [-j N] [testname ...]
exec tests/test-vdx.sh "$@"
