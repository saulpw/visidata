'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand, vd

@Sheet.api
def slide_col(sheet, colidx, newcolidx):
    vd.addUndo(moveVisibleCol, sheet, newcolidx, colidx)
    return moveVisibleCol(sheet, colidx, newcolidx)

@Sheet.api
def slide_keycol(sheet, fromKeyColIdx, toKeyColIdx):
    vd.addUndo(moveKeyCol, sheet, toKeyColIdx, fromKeyColIdx)
    return moveKeyCol(sheet, fromKeyColIdx, toKeyColIdx)


@Sheet.api
def slide_row(sheet, rowidx, newcolidx):
    vd.addUndo(moveListItem, sheet.rows, newcolidx, rowidx)
    return moveListItem(sheet.rows, rowidx, newcolidx)


@Sheet.api
def onClick(sheet, vcolidx, rowidx):
    pass

@Sheet.api
def onRelease(sheet, vcolidx, rowidx, destx, desty):
    newvcolidx = sheet.visibleColAtX(destx)
    newrowidx = sheet.visibleRowAtY(desty)

    if newvcolidx is not None and newvcolidx != vcolidx:
        sheet.cursorVisibleColIndex = sheet.slide_col(vcolidx, newvcolidx)

    # else: only move row if within same column (if column not moved above)
    elif newrowidx is not None and newrowidx != rowidx:
        sheet.cursorRowIndex = sheet.slide_row(rowidx, newrowidx)

    else:
        sheet.onClick(vcolidx, rowidx)


def moveKeyCol(sheet, fromKeyColIdx, toKeyColIdx):
    'Move key column to another key column position in sheet.'
    if not (1 <= toKeyColIdx <= len(sheet.keyCols)):
        vd.warning('already at edge')
        return fromKeyColIdx-1

    for col in sheet.keyCols:
        if col.keycol == fromKeyColIdx:
            col.keycol = toKeyColIdx
        elif toKeyColIdx < fromKeyColIdx:  # moving to the left
            if toKeyColIdx <= col.keycol < fromKeyColIdx:
                col.keycol += 1
        else:  # moving to the right
            if fromKeyColIdx < col.keycol <= toKeyColIdx:
                col.keycol -= 1

    # key columns are 1-indexed; columns in general are 0-indexed
    return toKeyColIdx-1


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    # a regular column cannot move to the left of keycols
    if 0 <= toVisColIdx < sheet.nVisibleCols:
        fromVisColIdx = min(max(fromVisColIdx, 0), sheet.nVisibleCols-1)
        fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
        if toVisColIdx < len(sheet.keyCols):
            vd.warning('already at edge')
            return fromVisColIdx
        else:
            toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
        moveListItem(sheet.columns, fromColIdx, toColIdx)
        return toVisColIdx
    else:
        vd.warning('already at edge')
        return fromVisColIdx


Sheet.addCommand('H', 'slide-left', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex-1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, cursorCol.keycol-1)', 'slide current column left')
Sheet.addCommand('L', 'slide-right', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex+1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, cursorCol.keycol+1)', 'slide current column right')
Sheet.addCommand('J', 'slide-down', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex+1)', 'slide current row down')
Sheet.addCommand('K', 'slide-up', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex-1)', 'slide current row up')
Sheet.addCommand('gH', 'slide-leftmost', 'slide_col(cursorVisibleColIndex, len(keyCols) + 0) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, 1)', 'slide current column all the way to the left of sheet')
Sheet.addCommand('gL', 'slide-rightmost', 'slide_col(cursorVisibleColIndex, nVisibleCols-1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, len(keyCols))', 'slide current column all the way to the right of sheet')
Sheet.addCommand('gJ', 'slide-bottom', 'slide_row(cursorRowIndex, nRows)', 'slide current row all the way to the bottom of sheet')
Sheet.addCommand('gK', 'slide-top', 'slide_row(cursorRowIndex, 0)', 'slide current row to top of sheet')
Sheet.addCommand('zH', 'slide-left-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex-int(input("slide col left n=", value=1)))', 'slide current column N positions to the left')
Sheet.addCommand('zL', 'slide-right-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex+int(input("slide col left n=", value=1)))', 'slide current column N positions to the right')
Sheet.addCommand('zJ', 'slide-down-n', 'slide_row(cursorRowIndex, cursorRowIndex+int(input("slide row down n=", value=1)))', 'slide current row N positions down')
Sheet.addCommand('zK', 'slide-up-n', 'slide_row(cursorRowIndex, cursorRowIndex-int(input("slide row up n=", value=1)))', 'slide current row N positions up')

Sheet.bindkey('KEY_SLEFT', 'slide-left')
Sheet.bindkey('KEY_SR', 'slide-up')
Sheet.bindkey('kDN', 'slide-down')
Sheet.bindkey('kUP', 'slide-up')
Sheet.bindkey('KEY_SRIGHT', 'slide-right')
Sheet.bindkey('KEY_SF', 'slide-down')

Sheet.bindkey('gKEY_SLEFT', 'slide-leftmost')
Sheet.bindkey('gkDN', 'slide-bottom')
Sheet.bindkey('gkUP', 'slide-top')
Sheet.bindkey('gKEY_SRIGHT', 'slide-rightmost')
