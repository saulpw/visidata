from visidata import *


@VisiData.api
@asyncthread
def fillNullValues(vd, col, rows):
    'Fill null cells in col with the previous non-null value'
    lastval = None
    oldvals = [] # for undo
    isNull = col.sheet.isNullFunc()
    n = 0
    rowsToFill = [id(r) for r in rows]
    for r in Progress(col.sheet.rows, 'filling'):  # loop over all rows
        try:
            val = col.getValue(r)
        except Exception as e:
            val = e

        if isNull(val):
            if lastval and (id(r) in rowsToFill):
                oldvals.append((col,r,val))
                col.setValue(r, lastval)
                n += 1
        else:
            lastval = val

    def _undo():
        for c, r, v in oldvals:
            c.setValue(r, v)
    vd.addUndo(_undo)

    col.recalc()
    vd.status("filled %d values" % n)


Sheet.addCommand('f', 'setcol-fill', 'fillNullValues(cursorCol, someSelectedRows)', 'fills null cells in selected rows of current column with contents of non-null cells up the current column')
