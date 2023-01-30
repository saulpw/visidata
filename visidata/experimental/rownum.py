from visidata import *
from functools import wraps, partial


@asyncthread
@Sheet.api
def calcRowIndex(sheet, indexes):
    for rownum, r in enumerate(sheet.rows):
        indexes[sheet.rowid(r)] = rownum


@Sheet.lazy_property
def _rowindex(sheet):
    ret = {}
    sheet.calcRowIndex(ret)
    return ret


@Sheet.api
def rowindex(sheet, row):
    'Returns the rowindex given the row.  May spawn a thread to compute underlying _rowindex.'
    return sheet._rowindex.get(sheet.rowid(row))


@Sheet.api
def prev(sheet, row):
    'Return the row previous to the given row.'
    rownum = max(sheet.rowindex(row)-1, 0)
    return LazyComputeRow(sheet, sheet.rows[rownum])


@Sheet.api
def addcol_rowindex(sheet, newcol):
    oldAddRow = sheet.addRow
    def rownum_addRow(sheet, col, row, index=None):
        if index is None:
            index = len(sheet.rows)

        col._rowindex[sheet.rowid(row)] = index
        return oldAddRow(row, index)

    # wrapper addRow to keep the index up to date
    sheet.addRow = wraps(oldAddRow)(partial(rownum_addRow, sheet, newcol))
    sheet.addColumnAtCursor(newcol)

    # spawn a little thread to calc the rowindex
    sheet.calcRowIndex(newcol._rowindex)


@Sheet.api
def addcol_delta(sheet, vcolidx):
    col = sheet.visibleCols[vcolidx]

    newcol = ColumnExpr("delta_"+col.name,
                   type=col.type,
                   _rowindex={},    # [rowid(row)] -> rowidx
                   expr="{0}-prev(row).{0}".format(col.name))

    sheet.addcol_rowindex(newcol)
    return newcol

@Sheet.api
def addcol_rownum(sheet):
    newcol = Column("rownum",
               type=int,
               _rowindex={},    # [rowid(row)] -> rowidx
               getter=lambda col,row: col._rowindex.get(col.sheet.rowid(row)))

    sheet.addcol_rowindex(newcol)
    return newcol

Sheet.addCommand(None, 'addcol-rownum', 'addcol_rownum()', helpstr='add column with original row ordering')
Sheet.addCommand(None, 'addcol-delta', 'addcol_delta(cursorVisibleColIndex)', helpstr='add column with delta of current column')
