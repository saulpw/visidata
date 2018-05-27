'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand

Sheet.Command('H', 'i = sheet.cursorVisibleColIndex; sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i-1)', 'slide current column left', 'slide-col-left')
Sheet.Command('L', 'i = sheet.cursorVisibleColIndex; sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i+1)', 'slide current column right', 'slide-col-right')
Sheet.Command('J', 'i = sheet.cursorRowIndex; sheet.cursorRowIndex = moveListItem(rows, i, i+1)', 'slide current row down', 'slide-row-down')
Sheet.Command('K', 'i = sheet.cursorRowIndex; sheet.cursorRowIndex = moveListItem(rows, i, i-1)', 'slide current row up', 'slide-row-up')
Sheet.Command('gH', 'columns.insert(0, columns.pop(cursorColIndex))', 'slide current column all the way to the left of sheet', 'slide-col-leftmost')
Sheet.Command('gL', 'columns.append(columns.pop(cursorColIndex))', 'slide current column all the way to the right of sheet', 'slide-col-rightmost')
Sheet.Command('gJ', 'rows.append(rows.pop(cursorRowIndex))', 'slide current row to the bottom of sheet', 'slide-row-bottom')
Sheet.Command('gK', 'rows.insert(0, rows.pop(cursorRowIndex))', 'slide current row the top of sheet', 'slide-row-top')
Sheet.Command('zH', 'i = sheet.cursorVisibleColIndex; n=int(input("slide col left n=", value=1)); sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i-n)', 'slide current column left n', 'slide-col-left-n')
Sheet.Command('zL', 'i = sheet.cursorVisibleColIndex; n=int(input("slide col right n=", value=1)); sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i+n)', 'slide current column right n', 'slide-col-right-n')
Sheet.Command('zJ', 'i = sheet.cursorRowIndex; n=int(input("slide row down n=", value=1)); sheet.cursorRowIndex = moveListItem(rows, i, i+n)', 'slide current row down n', 'slide-row-down-n')
Sheet.Command('zK', 'i = sheet.cursorRowIndex; n=int(input("slide row up n=", value=1)); sheet.cursorRowIndex = moveListItem(rows, i, i-n)', 'slide current row up n', 'slide-row-up-n')


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    toVisColIdx = min(max(toVisColIdx, 0), sheet.nVisibleCols)
    fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
    toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
    moveListItem(sheet.columns, fromColIdx, toColIdx)
    return toVisColIdx
