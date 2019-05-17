from visidata import Sheet, bindkey

# vim-style scrolling with the 'z' prefix
Sheet.addCommand('zz', 'scroll-middle', 'sheet.topRowIndex = cursorRowIndex-int(nVisibleRows/2)')
Sheet.addCommand(None, 'page-right', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex')
Sheet.addCommand(None, 'page-left', 'pageLeft()')
Sheet.addCommand('zh', 'scroll-left', 'sheet.cursorVisibleColIndex -= options.scroll_incr')
Sheet.addCommand('zl', 'scroll-right', 'sheet.cursorVisibleColIndex += options.scroll_incr')
Sheet.addCommand(None, 'scroll-leftmost', 'sheet.leftVisibleColIndex = cursorVisibleColIndex')
Sheet.addCommand(None, 'scroll-rightmost', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp')

Sheet.addCommand(None, 'go-end',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1')
Sheet.addCommand(None, 'go-home', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0')

bindkey('CTRL-BUTTON4_PRESSED', 'scroll-left')
bindkey('CTRL-REPORT_MOUSE_POSITION', 'scroll-right')

bindkey('zk', 'scroll-up')
bindkey('zj', 'scroll-down')
bindkey('zKEY_UP', 'scroll-up')
bindkey('zKEY_DOWN', 'scroll-down')
bindkey('zKEY_LEFT', 'scroll-left')
bindkey('zKEY_RIGHT', 'scroll-right')
