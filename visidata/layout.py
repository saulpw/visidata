from visidata import VisiData, vd, Column, Sheet, Fanout

@Column.api
def setWidth(self, w):
    if self.width != w:
        if self.width == 0 or w == 0:  # hide/unhide
            vd.addUndo(setattr, self, '_width', self.width)
    self._width = w


@Column.api
def toggleWidth(self, width):
    'Change column width to either given `width` or default value.'
    if self.width != width:
        self.width = width
    else:
        self.width = int(self.sheet.options.default_width)


@Column.api
def toggleVisibility(self):
    if self.height == 1:
        self.height = self.sheet.options.default_height
    else:
        self.height = 1

@VisiData.api
def unhide_cols(vd, cols, rows):
    'sets appropriate width if column was either hidden (0) or unseen (None)'
    for c in cols:
        c.setWidth(abs(c.width or 0) or c.getMaxWidth(rows))


Sheet.addCommand('_', 'resize-col-max', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))', 'toggle width of current column between full and default width'),
Sheet.addCommand('z_', 'resize-col-input', 'width = int(input("set width= ", value=cursorCol.width)); cursorCol.setWidth(width)', 'adjust width of current column to N')
Sheet.addCommand('g_', 'resize-cols-max', 'for c in visibleCols: c.setWidth(c.getMaxWidth(visibleRows))', 'toggle widths of all visible clumns between full and default width'),
Sheet.addCommand('gz_', 'resize-cols-input', 'width = int(input("set width= ", value=cursorCol.width)); Fanout(visibleCols).setWidth(width)', 'adjust widths of all visible columns to N')

Sheet.addCommand('-', 'hide-col', 'cursorCol.hide()', 'Hide current column')
Sheet.addCommand('z-', 'resize-col-half', 'cursorCol.setWidth(cursorCol.width//2)', 'reduce width of current column by half'),

Sheet.addCommand('gv', 'unhide-cols', 'unhide_cols(columns, visibleRows)', 'Show all columns')
Sheet.addCommand('v', 'visibility-sheet', 'for c in visibleCols: c.toggleVisibility()')
Sheet.addCommand('zv', 'visibility-col', 'cursorCol.toggleVisibility()')
