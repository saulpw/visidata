#!/usr/bin/env python3

import sys
import os.path

kwargs = {}

for arg in sys.argv[1:]:
    k, v = arg.split('=', maxsplit=1)
    if os.path.exists(v):
        v = open(v).read()
    kwargs[k] = v

sys.stdout.write(sys.stdin.read().format(**kwargs))
