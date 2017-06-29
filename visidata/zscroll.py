from visidata import *

# vim-style scrolling with the 'z' prefix

command('zk', 'sheet.topRowIndex -= 1', 'scroll one line up')
command('zj', 'sheet.topRowIndex += 1', 'scroll one line down')
command('zt', 'sheet.topRowIndex = cursorRowIndex', 'scroll cursor row to top of screen')
command('zz', 'sheet.topRowIndex = cursorRowIndex-int(nVisibleRows/2)', 'scroll cursor row to middle of screen')
command('zb', 'sheet.topRowIndex = cursorRowIndex-nVisibleRows+1', 'scroll cursor row to bottom of screen')
command(['zL', 'kRIT5'], 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex', 'scroll columns one page to the right')
command(['zH', 'kLFT5'], 'pageLeft()', 'scroll columns one page to the left')
command(['zh', 'zKEY_LEFT'], 'sheet.leftVisibleColIndex -= 1', 'scroll columns one to the left')
command(['zl', 'zKEY_RIGHT'], 'sheet.leftVisibleColIndex += 1', 'scroll columns one to the right')
command('zs', 'sheet.leftVisibleColIndex = cursorVisibleColIndex', 'scroll cursor to leftmost column')
command('ze', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp', 'scroll cursor to rightmost column')

command('zKEY_END',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to last row and last column')
command('zKEY_HOME', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0', 'go to top row and top column')
