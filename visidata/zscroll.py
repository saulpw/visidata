from .vdtui import *

# vim-style scrolling with the 'z' prefix

globalCommand('zk', 'sheet.topRowIndex -= 1', 'scroll one line up')
globalCommand('zj', 'sheet.topRowIndex += 1', 'scroll one line down')
globalCommand('zt', 'sheet.topRowIndex = cursorRowIndex', 'scroll cursor row to top of screen')
globalCommand('zz', 'sheet.topRowIndex = cursorRowIndex-int(nVisibleRows/2)', 'scroll cursor row to middle of screen')
globalCommand('zb', 'sheet.topRowIndex = cursorRowIndex-nVisibleRows+1', 'scroll cursor row to bottom of screen')
globalCommand(['zL', 'kRIT5'], 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex', 'scroll columns one page to the right')
globalCommand(['zH', 'kLFT5'], 'pageLeft()', 'scroll columns one page to the left')
globalCommand(['zh', 'zKEY_LEFT'], 'sheet.leftVisibleColIndex -= 1', 'scroll columns one to the left')
globalCommand(['zl', 'zKEY_RIGHT'], 'sheet.leftVisibleColIndex += 1', 'scroll columns one to the right')
globalCommand('zs', 'sheet.leftVisibleColIndex = cursorVisibleColIndex', 'scroll cursor to leftmost column')
globalCommand('ze', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp', 'scroll cursor to rightmost column')

globalCommand('zKEY_END',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to last row and last column')
globalCommand('zKEY_HOME', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0', 'go to top row and top column')

#globalCommand('0', 'gh')
