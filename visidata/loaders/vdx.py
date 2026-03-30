import json
import re

import visidata
from visidata import VisiData, CommandLogBase, BaseSheet, Sheet, AttrDict, Progress

VDX_VD_COLUMNS = ['sheet', 'col', 'row', 'longname', 'input', 'keystrokes', 'comment']


@VisiData.api
def open_vdx(vd, p):
    return CommandLogSimple(p.base_stem, source=p, precious=True)


VDX_CONTEXT_COMMANDS = {'sheet', 'col', 'row'}

class CommandLogSimple(CommandLogBase, Sheet):
    filetype = 'vdx'
    def iterload(self):
        context = {}  # pending sheet/col/row for next command
        for line in self.source:
            if not line or line[0] == '#':
                continue
            if line[0] == '{':
                # .vdj json line
                yield AttrDict(json.loads(line))
                context = {}
            elif '\t' in line:
                # .vd tsv line; skip header
                fields = line.split('\t')
                if fields == VDX_VD_COLUMNS[:len(fields)]:
                    continue
                d = {k: v for k, v in zip(VDX_VD_COLUMNS, fields) if v}
                yield AttrDict(d)
                context = {}
            else:
                # .vdx minimal line
                longname, *rest = line.split(' ', maxsplit=1)
                if longname == 'replay-reset':
                    context = {}
                    yield AttrDict(longname=longname,
                                   input=rest[0] if rest else '')
                elif longname in VDX_CONTEXT_COMMANDS:
                    context[longname] = rest[0] if rest else ''
                elif longname == 'option':
                    # option scope name value -> set-option
                    parts = (rest[0] if rest else '').split(' ', maxsplit=2)
                    scope = parts[0] if len(parts) > 0 else 'global'
                    name = parts[1] if len(parts) > 1 else ''
                    value = parts[2] if len(parts) > 2 else ''
                    yield AttrDict(longname='set-option',
                                   sheet=scope, col='', row=name, input=value)
                else:
                    yield AttrDict(longname=longname,
                                   input=rest[0] if rest else '',
                                   **context)
                    context = {}


@VisiData.api
def save_vdx(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        fp.write(f"#!/usr/bin/env -S vd -p\n")
        fp.write(f"# {visidata.__version_info__}\n")
        for vs in vsheets:
            prevrow = None
            for r in vs.rows:
                if prevrow is not None and r.sheet and prevrow.sheet != r.sheet:
                    fp.write(f'sheet {r.sheet}\n')
                if r.col and (prevrow is None or prevrow.col != r.col):
                    fp.write(f'col {r.col}\n')
                if r.row and (prevrow is None or prevrow.row != r.row):
                    fp.write(f'row {r.row}\n')

                line = r.longname
                if r.input:
                    line += ' ' + str(r.input)
                fp.write(line + '\n')

                prevrow = r


@VisiData.api
def runvdx(vd, vdx:str):
    for line in Progress(vdx.splitlines()):
        vs = vd.sheet or Sheet()
        vd.sync(vs.ensureLoaded())
        line = line.strip()
        if not line or line[0] == '#':
            continue

        m = re.match(r'^(\+(\S+) )?(\S+)(.*)$', line)
        if not m:
            print('bad:', line)
            continue

        _, pos, longname, rest = m.groups()
        vd.currentReplayRow = AttrDict(longname=longname, input=rest)
        if pos:
            vd.moveToPos(vd.sheets, *vd.parsePos(pos))
        print(vs.name, longname)
        vs.execCommand(longname)
        vd.sync()


