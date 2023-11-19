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
def toggleMultiline(self):
    if self.height == 1:
        self.height = self.sheet.options.default_height
    else:
        self.height = 1

@VisiData.api
def unhide_cols(vd, cols, rows):
    'sets appropriate width if column was either hidden (0) or unseen (None)'
    for c in cols:
        c.setWidth(abs(c.width or 0) or c.getMaxWidth(rows))

@VisiData.api
def hide_col(vd, col):
    if not col: vd.fail("no columns to hide")
    col.hide()

Sheet.addCommand('_', 'resize-col-max', 'if cursorCol: cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))', 'toggle width of current column between full and default width')
Sheet.addCommand('z_', 'resize-col-input', 'width = int(input("set width= ", value=cursorCol.width)); cursorCol.setWidth(width)', 'adjust width of current column to N')
Sheet.addCommand('g_', 'resize-cols-max', 'for c in visibleCols: c.setWidth(c.getMaxWidth(visibleRows))', 'toggle widths of all visible columns between full and default width')
Sheet.addCommand('gz_', 'resize-cols-input', 'width = int(input("set width= ", value=cursorCol.width)); Fanout(visibleCols).setWidth(width)', 'adjust widths of all visible columns to N')

Sheet.addCommand('-', 'hide-col', 'hide_col(cursorCol)', 'Hide current column')
Sheet.addCommand('z-', 'resize-col-half', 'cursorCol.setWidth(cursorCol.width//2)', 'reduce width of current column by half')

Sheet.addCommand('gv', 'unhide-cols', 'unhide_cols(columns, visibleRows)', 'Unhide all hidden columns')
Sheet.addCommand('v', 'toggle-multiline', 'for c in visibleCols: c.toggleMultiline()', 'toggle multiline display')
Sheet.addCommand('zv', 'resize-height-input', 'Fanout(visibleCols).height=int(input("set height for all columns to: ", value=max(c.height for c in sheet.visibleCols)))', 'resize row height to N')
Sheet.addCommand('gzv', 'resize-height-max', 'h=calc_height(cursorRow, {}, maxheight=windowHeight-1); vd.status(f"set height for all columns to {h}"); Fanout(visibleCols).height=h', 'resize row height to max height needed to see this row')

vd.addMenuItems('''
    Column > Hide > hide-col
    Column > Unhide all > unhide-cols
    Column > Resize > half width > resize-col-half
    Column > Resize > current column width to max > resize-col-max
    Column > Resize > current column width to N > resize-col-input
    Column > Resize > all columns width to max > resize-cols-max
    Column > Resize > all columns width to N > resize-cols-input
    Row > Resize > height to N > resize-height-input
    Row > Resize > height to max > resize-height-max
    View > Toggle display > multiline > toggle-multiline
''')
