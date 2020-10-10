#!/usr/bin/env python3
'''
Get the hash of a .py plugin file so that it can be added to plugins.jsonl.

Mirror VisiData's runtime hash checking behavior:
https://github.com/saulpw/visidata/blob/v2.-4/visidata/plugins.py#L45-L47
'''

import hashlib
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <file>')
    sys.exit(1)

try:
    p = Path(sys.argv[1])
    print(hashlib.sha256(p.read_bytes().strip()).hexdigest(), sep='')
except FileNotFoundError as err:
    print(f"Can't find file: {err.filename}")
    sys.exit(1)
