'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand, vd

@Sheet.api
def slide_col(sheet, colidx, newcolidx):
    vd.addUndo(moveVisibleCol, sheet, newcolidx, colidx)
    return moveVisibleCol(sheet, colidx, newcolidx)

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


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    if 0 <= toVisColIdx < sheet.nVisibleCols:
        fromVisColIdx = min(max(fromVisColIdx, 0), sheet.nVisibleCols-1)
        fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
        # a regular column cannot move to the left of keycols
        if toVisColIdx <= sheet.nKeys:
            toColIdx = sheet.columns.index(sheet.nonKeyVisibleCols[toVisColIdx])
        else:
            toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
        moveListItem(sheet.columns, fromColIdx, toColIdx)
        return toVisColIdx
    else:
        vd.fail('already at edge')


Sheet.addCommand('H', 'slide-left', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex-1)', 'slide current column left')
Sheet.addCommand('L', 'slide-right', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex+1)', 'slide current column right')
Sheet.addCommand('J', 'slide-down', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex+1)', 'slide current row down')
Sheet.addCommand('K', 'slide-up', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex-1)', 'slide current row up')
Sheet.addCommand('gH', 'slide-leftmost', 'slide_col(cursorVisibleColIndex, 0)', 'slide current column all the way to the left of sheet')
Sheet.addCommand('gL', 'slide-rightmost', 'slide_col(cursorVisibleColIndex, nVisibleCols-1)', 'slide current column all the way to the right of sheet')
Sheet.addCommand('gJ', 'slide-bottom', 'slide_row(cursorRowIndex, nRows)', 'slide current row all the way to the bottom of sheet')
Sheet.addCommand('gK', 'slide-top', 'slide_row(cursorRowIndex, 0)', 'slide current row to top of sheet')
Sheet.addCommand('zH', 'slide-left-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex-int(input("slide col left n=", value=1)))', 'slide current column N positions to the left')
Sheet.addCommand('zL', 'slide-right-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex+int(input("slide col left n=", value=1)))', 'slide current column N positions to the right')
Sheet.addCommand('zJ', 'slide-down-n', 'slide_row(cursorRowIndex, cursorRowIndex+int(input("slide row down n=", value=1)))', 'slide current row N positions down')
Sheet.addCommand('zK', 'slide-up-n', 'slide_row(cursorRowIndex, cursorRowIndex-int(input("slide row up n=", value=1)))', 'slide current row N positions up')

Sheet.addCommand('BUTTON1_RELEASED','release-mouse','onRelease(cursorVisibleColIndex, cursorRowIndex, mouseX, mouseY)', 'slide current row/column to mouse cursor release position')
