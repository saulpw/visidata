from visidata import *
from difflib import SequenceMatcher

theme('color_diff', 'red', 'color of values different from --diff source')
theme('color_diff_add', 'yellow', 'color of rows/columns added to --diff source')

globalCommand(None, 'setdiff-sheet', 'setDiffSheet(sheet)')

class DiffRow(list):
    def __hash__(self):
        return hash(u"\uFDD0".join(self))

def loaddiff(base, dif):
    base.rows = [DiffRow(x) for x in base.rows]
    dif.rows = [DiffRow(x) for x in dif.rows]   # or do this before?
    m = SequenceMatcher(a=dif.rows, b=base.rows)
    for t, astart, aend, bstart, bend in m.get_opcodes():
        alen = aend - astart
        blen = bend - bstart
        if t == 'replace':
            for i in range(min(alen, blen)):
                base.rows[bstart+i].alternate = dif.rows[astart+i]
            for i in range(blen - alen):
                base.rows[bstart+i+alen].inserted = True
        elif t == 'insert':
            for i in range(blen):
                base.rows[bstart + i].inserted = True

def makeDiffColorizer(othersheet):
    def colorizeDiffs(sheet, col, row, cellval):
        if sheet is othersheet or sheet is None:
            return None
        if not hasattr(sheet, 'diffloaded'):
            try:
                loaddiff(sheet, othersheet)
            except Exception as e:
                pass
            sheet.diffloaded = True
            print("Loaded")
        if hasattr(row, 'alternate'):
            vcolidx = sheet.visibleCols.index(col)
            if vcolidx < len(row.alternate):
                if row.alternate[vcolidx] != cellval.value:
                    return options.color_diff
        elif hasattr(row, 'inserted'):
            return options.color_diff_add
    return colorizeDiffs


def setDiffSheet(vs):
    Sheet.colorizers.append(CellColorizer(8, None, makeDiffColorizer(vs)))
