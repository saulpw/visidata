from visidata import theme, globalCommand, Sheet, CellColorizer

theme('color_diff', 'red', 'color of values different from --diff source')
theme('color_diff_add', 'yellow', 'color of rows/columns added to --diff source')

globalCommand(None, 'setdiff-sheet', 'setDiffSheet(sheet)')


def makeDiffColorizer(othersheet):
    def colorizeDiffs(sheet, col, row, cellval):
        if not row or not col:
            return None
        vcolidx = sheet.visibleCols.index(col)
        rowidx = sheet.rows.index(row)
        if vcolidx < len(othersheet.visibleCols) and rowidx < len(othersheet.rows):
            otherval = othersheet.visibleCols[vcolidx].getValue(othersheet.rows[rowidx])
            if cellval.value != otherval:
                return 'color_diff'
        else:
            return 'color_diff_add'
    return colorizeDiffs


def setDiffSheet(vs):
    Sheet.colorizers.append(CellColorizer(8, None, makeDiffColorizer(vs)))
