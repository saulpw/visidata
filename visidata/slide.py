'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand

Sheet.addCommand('H', 'slide-left', 'i = sheet.cursorVisibleColIndex; sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i-1)')
Sheet.addCommand('L', 'slide-right', 'i = sheet.cursorVisibleColIndex; sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i+1)')
Sheet.addCommand('J', 'slide-down', 'i = sheet.cursorRowIndex; sheet.cursorRowIndex = moveListItem(rows, i, i+1)')
Sheet.addCommand('K', 'slide-up', 'i = sheet.cursorRowIndex; sheet.cursorRowIndex = moveListItem(rows, i, i-1)')
Sheet.addCommand('gH', 'slide-leftmost', 'columns.insert(0, columns.pop(cursorColIndex))')
Sheet.addCommand('gL', 'slide-rightmost', 'columns.append(columns.pop(cursorColIndex))')
Sheet.addCommand('gJ', 'slide-bottom', 'rows.append(rows.pop(cursorRowIndex))')
Sheet.addCommand('gK', 'slide-top', 'rows.insert(0, rows.pop(cursorRowIndex))')
Sheet.addCommand('zH', 'slide-left-n', 'i = sheet.cursorVisibleColIndex; n=int(input("slide col left n=", value=1)); sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i-n)')
Sheet.addCommand('zL', 'slide-right-n', 'i = sheet.cursorVisibleColIndex; n=int(input("slide col right n=", value=1)); sheet.cursorVisibleColIndex = moveVisibleCol(sheet, i, i+n)')
Sheet.addCommand('zJ', 'slide-down-n', 'i = sheet.cursorRowIndex; n=int(input("slide row down n=", value=1)); sheet.cursorRowIndex = moveListItem(rows, i, i+n)')
Sheet.addCommand('zK', 'slide-up-n', 'i = sheet.cursorRowIndex; n=int(input("slide row up n=", value=1)); sheet.cursorRowIndex = moveListItem(rows, i, i-n)')


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    toVisColIdx = min(max(toVisColIdx, 0), sheet.nVisibleCols)
    fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
    toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
    moveListItem(sheet.columns, fromColIdx, toColIdx)
    return toVisColIdx
