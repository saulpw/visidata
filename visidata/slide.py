'''slide rows/columns around'''

from visidata import Sheet, moveListItem, globalCommand


def _moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
    toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
    return moveListItem(sheet.columns, fromColIdx, toColIdx)

def slide_col_left(sheet, n=1):
    'slide current column left'
    i = sheet.cursorVisibleColIndex
    sheet.cursorVisibleColIndex = _moveVisibleCol(sheet, i, max(i-1, 0))

def slide_col_right(sheet, n=1):
    'slide current column right'
    i = sheet.cursorVisibleColIndex
    sheet.cursorVisibleColIndex = _moveVisibleCol(sheet, i, min(i+1, sheet.nVisibleCols-1))

def slide_row_down(sheet, n=1):
    'slide current row down'
    i = sheet.cursorRowIndex
    sheet.cursorRowIndex = moveListItem(sheet.rows, i, min(i+1, sheet.nRows-1))

def slide_row_up(sheet, n=1):
    'slide current row up'
    i = sheet.cursorRowIndex
    sheet.cursorRowIndex = moveListItem(sheet.rows, i, max(i-1, 0))

def slide_col_leftmost(sheet):
    'slide current column all the way to the left of sheet'
    moveListItem(sheet.columns, sheet.cursorColIndex, 0)

def slide_col_rightmost(sheet):
    'slide current column all the way to the right of sheet'
    moveListItem(sheet.columns, sheet.cursorColIndex, sheet.nCols)

def slide_row_bottom(sheet):
    'slide current row to the bottom of sheet'
    moveListItem(sheet.rows, sheet.cursorRowIndex, sheet.nRows)

def slide_row_top(sheet):
    'slide current row the top of sheet'
    moveListItem(sheet.rows, sheet.cursorRowIndex, 0)


Sheet.bind('H', slide_col_left)
Sheet.bind('L', slide_col_right)
Sheet.bind('J', slide_row_down)
Sheet.bind('K', slide_row_up)
Sheet.bind('gH', slide_col_leftmost)
Sheet.bind('gL', slide_col_rightmost)
Sheet.bind('gJ', slide_row_bottom)
Sheet.bind('gK', slide_row_top)

#menu('modify move column left', slide_col_left)

