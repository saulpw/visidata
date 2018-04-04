from visidata import *

option('color_diff', 'red', 'color of values different from --diff source')
option('color_diff_add', 'yellow', 'color of rows/columns added to --diff source')

globalCommand('', 'setDiffSheet(sheet)', 'set this sheet as the diff sheet for all new sheets', 'sheet-set-diff')


def makeDiffColorizer(othersheet):
    def colorizeDiffs(sheet, col, row, cellval):
        vcolidx = sheet.visibleCols.index(col)
        rowidx = sheet.rows.index(row)
        if vcolidx < len(othersheet.visibleCols) and rowidx < len(othersheet.rows):
            otherval = othersheet.visibleCols[vcolidx].getValue(othersheet.rows[rowidx])
            if cellval.value != otherval:
                return options.color_diff
        else:
            return options.color_diff_add
    return colorizeDiffs


def setDiffSheet(vs):
    Sheet.colorizers.append(Colorizer("cell", 8, makeDiffColorizer(vs)))
