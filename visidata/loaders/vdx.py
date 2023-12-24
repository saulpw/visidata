import re

import visidata
from visidata import VisiData, CommandLogBase, BaseSheet, Sheet, AttrDict, Progress


@VisiData.api
def open_vdx(vd, p):
    return CommandLogSimple(p.base_stem, source=p, precious=True)


class CommandLogSimple(CommandLogBase, Sheet):
    filetype = 'vdx'
    def iterload(self):
        for line in self.source:
            if not line or line[0] == '#':
                continue
            longname, *rest = line.split(' ', maxsplit=1)
            yield AttrDict(longname=longname,
                           input=rest[0] if rest else '')


@VisiData.api
def save_vdx(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
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
        vs.ensureLoaded()
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


BaseSheet.addCommand('', 'sheet', 'n=input("sheet to jump to: "); vd.push(vd.getSheet(n) or fail(f"no such sheet {n}"))', 'jump to named sheet')
BaseSheet.addCommand('', 'col', 'n=input("column to go to: "); moveToCol(n) or fail(f"no such column {n}")', 'move to named/numbered col')
BaseSheet.addCommand('', 'row', 'n=input("row to go to: "); moveToRow(n) or fail(f"no such row {n}")', 'move to named/numbered row')
