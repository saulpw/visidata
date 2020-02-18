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


Sheet.addCommand('H', 'slide-left', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex-1)')
Sheet.addCommand('L', 'slide-right', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex+1)')
Sheet.addCommand('J', 'slide-down', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex+1)')
Sheet.addCommand('K', 'slide-up', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex-1)')
Sheet.addCommand('gH', 'slide-leftmost', 'slide_col(cursorVisibleColIndex, 0)')
Sheet.addCommand('gL', 'slide-rightmost', 'slide_col(cursorVisibleColIndex, nVisibleCols-1)')
Sheet.addCommand('gJ', 'slide-bottom', 'slide_row(cursorRowIndex, nRows)')
Sheet.addCommand('gK', 'slide-top', 'slide_row(cursorRowIndex, 0)')
Sheet.addCommand('zH', 'slide-left-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex-int(input("slide col left n=", value=1)))')
Sheet.addCommand('zL', 'slide-right-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex+int(input("slide col left n=", value=1)))')
Sheet.addCommand('zJ', 'slide-down-n', 'slide_row(cursorRowIndex, cursorRowIndex+int(input("slide row down n=", value=1)))')
Sheet.addCommand('zK', 'slide-up-n', 'slide_row(cursorRowIndex, cursorRowIndex-int(input("slide row up n=", value=1)))')

Sheet.addCommand('BUTTON1_RELEASED','release-mouse','onRelease(cursorVisibleColIndex, cursorRowIndex, mouseX, mouseY)')

@Sheet.api
def onClick(sheet, vcolidx, rowidx):
    pass

@Sheet.api
def onRelease(sheet, vcolidx, rowidx, destx, desty):
    newvcolidx = sheet.visibleColAtX(destx)
    newrowidx = sheet.visibleRowAtY(desty)

    if newvcolidx is not None and newvcolidx != vcolidx:
        sheet.cursorVisibleColIndex = moveVisibleCol(sheet, vcolidx, newvcolidx)

    # else: only move row if within same column (if column not moved above)
    elif newrowidx is not None and newrowidx != rowidx:
        sheet.cursorRowIndex = moveListItem(sheet.rows, rowidx, newrowidx)

    else:
        sheet.onClick(vcolidx, rowidx)


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    if 0 <= toVisColIdx < sheet.nVisibleCols:
        fromVisColIdx = min(max(fromVisColIdx, 0), sheet.nVisibleCols-1)
        fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
        # a regular column cannot move to the left of keycols
        if toVisColIdx <= 0:
            toColIdx = sheet.columns.index(sheet.nonKeyVisibleCols[toVisColIdx])
        else:
            toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
        moveListItem(sheet.columns, fromColIdx, toColIdx)
        return toVisColIdx
    else:
        vd.fail('already at edge')
