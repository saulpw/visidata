from visidata import vd, Sheet, undoAttrCopy, Progress, option, asyncthread, options, rotateRange

__all__ = ['undoSheetSelection', 'undoSelection']

option('bulk_select_clear', False, 'clear selected rows before new bulk selections', replay=True)

Sheet.init('_selectedRows', dict)  # rowid(row) -> row

@Sheet.api
def isSelected(self, row):
    'True if given row is selected. O(log n).'
    return self.rowid(row) in self._selectedRows

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
    self._selectedRows[self.rowid(row)] = row

@Sheet.api
def unselectRow(self, row):
    'Unselect given row, return True if selected; else return False. O(log n)'
    if self.rowid(row) in self._selectedRows:
        del self._selectedRows[self.rowid(row)]
        return True
    else:
        return False

@Sheet.api
def clearSelected(self):
    'Removes all selected rows from selection, without calling unselectRow.  Override for sheet-specific selection implementation.'
    self._selectedRows.clear()

@Sheet.api
@asyncthread
def select(self, rows, status=True, progress=True):
    "Bulk select given rows. Don't show progress if progress=False; don't show status if status=False."
    before = self.nSelected
    if options.bulk_select_clear:
        self.clearSelected()
    for r in (Progress(rows, 'selecting') if progress else rows):
        self.selectRow(r)
    if status:
        if options.bulk_select_clear:
            msg = 'selected %s %s%s' % (self.nSelected, self.rowtype, ' instead' if before > 0 else '')
        else:
            msg = 'selected %s%s %s' % (self.nSelected-before, ' more' if before > 0 else '', self.rowtype)
        vd.status(msg)

@Sheet.api
@asyncthread
def unselect(self, rows, status=True, progress=True):
    "Unselect given rows. Don't show progress if progress=False; don't show status if status=False."
    before = self.nSelected
    for r in (Progress(rows, 'unselecting') if progress else rows):
        self.unselectRow(r)
    if status:
        vd.status('unselected %s/%s %s' % (before-self.nSelected, before, self.rowtype))

@Sheet.api
def selectByIdx(self, rowIdxs):
    'Select given row indexes, without progress bar.'
    self.select((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def unselectByIdx(self, rowIdxs):
    'Unselect given row indexes, without progress bar.'
    self.unselect((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def gatherBy(self, func, gerund='gathering'):
    'Generate only rows for which the given func returns True.'
    for i in Progress(rotateRange(self.nRows, self.cursorRowIndex), total=self.nRows, gerund=gerund):
        try:
            r = self.rows[i]
            if func(r):
                yield r
        except Exception:
            pass

@Sheet.property
def selectedRows(self):
    'List of selected rows in sheet order. [O(nRows*log(nSelected))]'
    if self.nSelected <= 1:
        return list(self._selectedRows.values())
    return [r for r in self.rows if self.rowid(r) in self._selectedRows]

@Sheet.property
def nSelected(self):
    'Number of selected rows.'
    return len(self._selectedRows)

@Sheet.api
@asyncthread
def deleteSelected(self):
    'Delete all selected rows.'
    ndeleted = self.deleteBy(self.isSelected)
    nselected = self.nSelected
    self.clearSelected()
    if ndeleted != nselected:
        vd.warning(f'deleted {ndeleted}, expected {nselected}')


undoSheetSelection = undoAttrCopy('[sheet]', '_selectedRows')

def undoSelection(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, '_selectedRows')


Sheet.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('s', 'select-row', 'selectRow(cursorRow); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)', undo=undoSheetSelection),

Sheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)', undo=undoSheetSelection),
Sheet.addCommand('gs', 'select-rows', 'select(rows)', undo=undoSheetSelection),
Sheet.addCommand('gu', 'unselect-rows', 'clearSelected()', undo=undoSheetSelection),

Sheet.addCommand('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zs', 'select-before', 'select(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzs', 'select-after', 'select(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])', undo=undoSheetSelection),

Sheet.addCommand('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("select regex: ", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("unselect regex: ", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("select regex: ", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),
Sheet.addCommand('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("unselect regex: ", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),

Sheet.addCommand(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', undo=undoSheetSelection),

Sheet.addCommand('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection)
