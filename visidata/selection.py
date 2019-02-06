from visidata import vd, Sheet, undoAttrCopy, Progress, replayableOption, asyncthread, options, rotate_range

__all__ = ['undoSheetSelection', 'undoSelection']

replayableOption('bulk_select_clear', False, 'clear selected rows before new bulk selections')

Sheet.init('_selectedRows', dict)  # id(row) -> row

@Sheet.api
def isSelected(self, row):
    'True if given row is selected. O(log n).'
    return id(row) in self._selectedRows

@Sheet.api
@asyncthread
def toggle(self, rows):
    'Toggle selection of given `rows`.'
    for r in Progress(rows, 'toggling', total=len(self.rows)):
        if not self.unselectRow(r):
            self.selectRow(r)

@Sheet.api
def selectRow(self, row):
    'Select given row. O(log n)'
    self._selectedRows[id(row)] = row

@Sheet.api
def unselectRow(self, row):
    'Unselect given row, return True if selected; else return False. O(log n)'
    if id(row) in self._selectedRows:
        del self._selectedRows[id(row)]
        return True
    else:
        return False

@Sheet.api
@asyncthread
def select(self, rows, status=True, progress=True):
    "Bulk select given rows. Don't show progress if progress=False; don't show status if status=False."
    before = len(self._selectedRows)
    if options.bulk_select_clear:
        self._selectedRows.clear()
    for r in (Progress(rows, 'selecting') if progress else rows):
        self.selectRow(r)
    if status:
        if options.bulk_select_clear:
            msg = 'selected %s %s%s' % (len(self._selectedRows), self.rowtype, ' instead' if before > 0 else '')
        else:
            msg = 'selected %s%s %s' % (len(self._selectedRows)-before, ' more' if before > 0 else '', self.rowtype)
        vd.status(msg)

@Sheet.api
@asyncthread
def unselect(self, rows, status=True, progress=True):
    "Unselect given rows. Don't show progress if progress=False; don't show status if status=False."
    before = len(self._selectedRows)
    for r in (Progress(rows, 'unselecting') if progress else rows):
        self.unselectRow(r)
    if status:
        vd.status('unselected %s/%s %s' % (before-len(self._selectedRows), before, self.rowtype))

@Sheet.api
def selectByIdx(self, rowIdxs):
    'Select given row indexes, without progress bar.'
    self.select((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def unselectByIdx(self, rowIdxs):
    'Unselect given row indexes, without progress bar.'
    self.unselect((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def gatherBy(self, func):
    'Generate only rows for which the given func returns True.'
    for i in rotate_range(len(self.rows), self.cursorRowIndex):
        try:
            r = self.rows[i]
            if func(r):
                yield r
        except Exception:
            pass

@Sheet.property
def selectedRows(self):
    'List of selected rows in sheet order. [O(nRows*log(nSelected))]'
    if len(self._selectedRows) <= 1:
        return list(self._selectedRows.values())
    return [r for r in self.rows if id(r) in self._selectedRows]

@Sheet.property
def nSelected(self):
    return len(self._selectedRows)

@Sheet.api
@asyncthread
def deleteSelected(self):
    'Delete all selected rows.'
    ndeleted = self.deleteBy(self.isSelected)
    nselected = len(self._selectedRows)
    self._selectedRows.clear()
    if ndeleted != nselected:
        error('expected %s' % nselected)

undoSheetSelection = undoAttrCopy('[sheet]', '_selectedRows')

def undoSelection(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, '_selectedRows')


Sheet.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('s', 'select-row', 'selectRow(cursorRow); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)', undo=undoSheetSelection),

Sheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)', undo=undoSheetSelection),
Sheet.addCommand('gs', 'select-rows', 'select(rows)', undo=undoSheetSelection),
Sheet.addCommand('gu', 'unselect-rows', '_selectedRows.clear()', undo=undoSheetSelection),

Sheet.addCommand('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zs', 'select-before', 'select(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzs', 'select-after', 'select(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])', undo=undoSheetSelection),

Sheet.addCommand('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),
Sheet.addCommand('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),

Sheet.addCommand(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', undo=undoSheetSelection),

Sheet.addCommand('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection)
