#!/usr/bin/env python3
'''Usage: dev/guide-check.py [-r] [GuideName ...]

Check guides in visidata/guides/ for references that render wrong in the GuideSheet.
With no names, check every guide.  With -r, also print the rendered text.
Exit status is the number of guides with problems.
'''

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import visidata
from visidata import vd, AttrDict, MissingAttrFormatter
from visidata.guide import CommandHelpGetter, OptionHelpGetter, parseGuide

GUIDE_WIDTH = 78
FRONT_MATTER_KEYS = {'sheettype'}


def check(name, render=False):
    path = visidata.Path(vd.pkg_resources_files(visidata)/f'guides/{name}.md')
    text = path.open(mode='r').read()
    problems = []

    metadata, body = parseGuide(text)
    for key in metadata:
        if key not in FRONT_MATTER_KEYS:
            problems.append(f'front matter: unknown key {key!r} (ignored by GuideSheet)')
    sheettype = metadata.sheettype

    sheetcls = vd.getGlobals().get(sheettype)
    if sheetcls is None:
        problems.append(f'front matter: sheettype {sheettype!r} is not a global')
        sheetcls = vd.getGlobals()['Sheet']

    cmds = CommandHelpGetter(sheetcls)
    opts = OptionHelpGetter()
    for m in re.finditer(r'\{help\.commands\.([\w.-]+)\}', body):
        try:
            found = MissingAttrFormatter().format('{help.commands.%s}' % m.group(1), help=AttrDict(commands=cmds))
        except Exception:
            found = ''
        if not found or found.startswith('{'):
            problems.append(f'unknown command for {sheettype}: {m.group(1)}')
    for m in re.finditer(r'\{help\.options\.([\w-]+)\}', body):
        if vd.options._get(m.group(1), 'default') is None:
            problems.append(f'unknown option: {m.group(1)}')

    for i, line in enumerate(body.splitlines(), start=1):
        bad = sorted(set(ch for ch in line if ord(ch) > 127))
        if bad:
            problems.append(f'line {i}: non-ASCII {"".join(bad)!r}')
        if re.search(r'[^.!?:\s] {2,}\S', line.strip()) and len(line.strip()) > GUIDE_WIDTH:
            problems.append(f'line {i}: preformatted line wider than {GUIDE_WIDTH} wraps')

    if render:
        helper = AttrDict(commands=cmds, options=opts)
        print(MissingAttrFormatter().format(body, help=helper, vd=vd))

    for p in problems:
        print(f'{name}: {p}')
    return bool(problems)


def main(args):
    render = '-r' in args
    names = [a for a in args if not a.startswith('-')]
    if not names:
        guidedir = visidata.Path(vd.pkg_resources_files(visidata)/'guides')
        names = sorted(p.stem for p in guidedir.iterdir() if p.suffix == '.md')
    return sum(check(n, render=render) for n in names)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
