from .vdtui import *

# vim-style scrolling with the 'z' prefix
globalCommand('zk', 'sheet.topRowIndex -= 1', 'scrolls one row up')
globalCommand('zj', 'sheet.topRowIndex += 1', 'scrolls one row down')
globalCommand('zt', 'sheet.topRowIndex = cursorRowIndex', 'scrolls current row to top of screen')
globalCommand('zz', 'sheet.topRowIndex = cursorRowIndex-int(nVisibleRows/2)', 'scrolls current row to center of screen')
globalCommand('zb', 'sheet.topRowIndex = cursorRowIndex-nVisibleRows+1', 'scrolls current row to bottom of screen')
globalCommand(['zL', 'kRIT5'], 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex', 'moves cursor one page right')
globalCommand(['zH', 'kLFT5'], 'pageLeft()', 'moves cursor one page left')
globalCommand(['zh', 'zKEY_LEFT'], 'sheet.leftVisibleColIndex -= 1', 'scrolls one column left')
globalCommand(['zl', 'zKEY_RIGHT'], 'sheet.leftVisibleColIndex += 1', 'scrolls one column right')
globalCommand('zs', 'sheet.leftVisibleColIndex = cursorVisibleColIndex', 'scrolls sheet to leftmost column')
globalCommand('ze', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp', 'scrolls sheet to rightmost column')

globalCommand('zKEY_END',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to last row and last column')
globalCommand('zKEY_HOME', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0', 'go to top row and top column')

#globalCommand('0', 'gh')
