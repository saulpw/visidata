from visidata import Column, Sheet, options, undoAttr


@Column.api
def toggleWidth(self, width):
    'Change column width to either given `width` or default value.'
    if self.width != width:
        self.width = width
    else:
        self.width = int(options.default_width)


@Column.api
def toggleVisibility(self):
    if self.height == 1:
        self.height = 10
    else:
        self.height = 1


Sheet.addCommand('_', 'resize-col-max', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))'),
Sheet.addCommand('z_', 'resize-col', 'cursorCol.width = int(input("set width= ", value=cursorCol.width))'),
Sheet.addCommand('g_', 'resize-cols-max', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)'),

Sheet.addCommand('-', 'hide-col', 'cursorCol.hide()', undo=undoAttr('[cursorCol]', 'width'))
Sheet.addCommand('z-', 'resize-col-half', 'cursorCol.width = cursorCol.width//2'),

Sheet.addCommand('gv', 'unhide-cols', 'for c in columns: c.width = abs(c.width or 0) or c.getMaxWidth(visibleRows)', undo=undoAttr('columns', 'width'))
Sheet.addCommand('v', 'visibility-sheet', 'for c in visibleCols: c.toggleVisibility()')
Sheet.addCommand('zv', 'visibility-col', 'cursorCol.toggleVisibility()')
