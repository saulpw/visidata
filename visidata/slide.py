'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand


def _moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
    toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
    moveListItem(sheet.columns, fromColIdx, toColIdx)
    return toVisColIdx


def slide_col_left(sheet, n=1):
    'slide current column left'
    i = sheet.cursorVisibleColIndex
    _moveVisibleCol(sheet, i, max(i-1, 0))
    sheet.cursorVisibleColIndex = i-1


def slide_col_right(sheet, n=1):
    'slide current column right'
    i = sheet.cursorVisibleColIndex
    _moveVisibleCol(sheet, i, min(i+1, sheet.nVisibleCols-1))
    sheet.cursorVisibleColIndex = i+1


def slide_col_leftmost(sheet):
    'slide current column all the way to the left of sheet'
    moveListItem(sheet.columns, sheet.cursorColIndex, 0)


Sheet.bind('H', slide_col_left)
Sheet.bind('L', slide_col_right)
#Sheet.bind('J', slide_row_up)
#Sheet.bind('K', slide_row_down)
Sheet.bind('gH', slide_col_leftmost)

#menu('modify move column left', slide_col_left)

globalCommand('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'move current row down', 'modify-move-row-down')
globalCommand('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'move current row up', 'modify-move-row-up')
globalCommand('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'slide current row to the bottom of sheet', 'modify-move-row-bottom')
globalCommand('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'slide current row all the way to the top of sheet', 'modify-move-row-top')
globalCommand('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'slide current column all the way to the right of sheet', 'modify-move-column-rightmost')
