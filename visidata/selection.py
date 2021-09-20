from visidata import vd, Sheet, Progress, asyncthread, options, rotateRange, Fanout, undoAttrCopyFunc, copy

vd.option('bulk_select_clear', False, 'clear selected rows before new bulk selections', replay=True)
vd.option('some_selected_rows', False, 'if no rows selected, if True, someSelectedRows returns all rows; if False, fails')

Sheet.init('_selectedRows', dict)  # rowid(row) -> row

@Sheet.api
def isSelected(self, row):
    'Return True if *row* is selected.'
    return self.rowid(row) in self._selectedRows

@Sheet.api
@asyncthread
def toggle(self, rows):
    'Toggle selection of given *rows*.  Async.'
    self.addUndoSelection()
    for r in Progress(rows, 'toggling', total=len(self.rows)):
        if not self.unselectRow(r):
            self.selectRow(r)

@Sheet.api
def selectRow(self, row):
    'Add *row* to set of selected rows.  Overrideable.'
    self._selectedRows[self.rowid(row)] = row

@Sheet.api
def unselectRow(self, row):
    'Remove *row* from set of selected rows.  Return True if row was previously selected.  Overrideable.'
    if self.rowid(row) in self._selectedRows:
        del self._selectedRows[self.rowid(row)]
        return True
    else:
        return False

@Sheet.api
def clearSelected(self):
    'Clear set of selected rows, without calling ``unselectRow`` for each one.'
    self.addUndoSelection()
    self._selectedRows.clear()

@Sheet.api
@asyncthread
def select(self, rows, status=True, progress=True):
    "Add *rows* to set of selected rows. Async. Don't show progress if *progress* is False; don't show status if *status* is False."
    self.addUndoSelection()
    before = self.nSelectedRows
    if options.bulk_select_clear:
        self.clearSelected()
    for r in (Progress(rows, 'selecting') if progress else rows):
        self.selectRow(r)
    if status:
        if options.bulk_select_clear:
            msg = 'selected %s %s%s' % (self.nSelectedRows, self.rowtype, ' instead' if before > 0 else '')
        else:
            msg = 'selected %s%s %s' % (self.nSelectedRows-before, ' more' if before > 0 else '', self.rowtype)
        vd.status(msg)

@Sheet.api
@asyncthread
def unselect(self, rows, status=True, progress=True):
    "Remove *rows* from set of selected rows. Async. Don't show progress if *progress* is False; don't show status if *status* is False."
    self.addUndoSelection()
    before = self.nSelectedRows
    for r in (Progress(rows, 'unselecting') if progress else rows):
        self.unselectRow(r)
    if status:
        vd.status('unselected %s/%s %s' % (before-self.nSelectedRows, before, self.rowtype))

@Sheet.api
def selectByIdx(self, rowIdxs):
    'Add rows indicated by row indexes in *rowIdxs* to set of selected rows.  Async.'
    self.select((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def unselectByIdx(self, rowIdxs):
    'Remove rows indicated by row indexes in *rowIdxs* from set of selected rows.  Async.'
    self.unselect((self.rows[i] for i in rowIdxs), progress=False)

@Sheet.api
def gatherBy(self, func, gerund='gathering'):
    'Generate rows for which ``func(row)`` returns True, starting from the cursor.'
    for i in Progress(rotateRange(self.nRows, self.cursorRowIndex-1), total=self.nRows, gerund=gerund):
        try:
            r = self.rows[i]
            if func(r):
                yield r
        except Exception as e:
            vd.exceptionCaught(e, status=False)

@Sheet.property
def selectedRows(self):
    'List of selected rows in sheet order.'
    if self.nSelectedRows <= 1:
        return Fanout(self._selectedRows.values())
    return Fanout((r for r in self.rows if self.rowid(r) in self._selectedRows))

@Sheet.property
def onlySelectedRows(self):
    'List of selected rows in sheet order.  Fail if no rows are selected.'
    if self.nSelectedRows == 0:
        vd.fail('no rows selected')
    return self.selectedRows

@Sheet.property
def someSelectedRows(self):
    '''Return a list of rows:
        (a) in batch mode, always return selectedRows
        (b) in interactive mode, if options.some_selected_rows is True, return selectedRows or all rows if none selected
        (c) in interactive mode, if options.some_selected_rows is False, return selectedRows or fail if none selected'''
    if options.batch:
        return self.selectedRows
    if options.some_selected_rows:
        return self.selectedRows or self.rows
    return self.onlySelectedRows

@Sheet.property
def nSelectedRows(self):
    'Number of selected rows.'
    return len(self._selectedRows)

@Sheet.api
@asyncthread
def deleteSelected(self):
    'Delete all selected rows.  Async.'
    ndeleted = self.deleteBy(self.isSelected)
    nselected = self.nSelectedRows
    self.clearSelected()
    if ndeleted != nselected:
        vd.warning(f'deleted {ndeleted}, expected {nselected}')


@Sheet.api
def addUndoSelection(sheet):
    vd.addUndo(undoAttrCopyFunc([sheet], '_selectedRows'))


Sheet.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)', 'toggle selection of current row')
Sheet.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)', 'select current row')
Sheet.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)', 'unselect current row')

Sheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)', 'toggle selection of all rows')
Sheet.addCommand('gs', 'select-rows', 'select(rows)', 'select all rows')
Sheet.addCommand('gu', 'unselect-rows', 'clearSelected()', 'unselect all rows')

Sheet.addCommand('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])', 'toggle selection of rows from top to cursor')
Sheet.addCommand('zs', 'select-before', 'select(rows[:cursorRowIndex])', 'select all rows from top to cursor')
Sheet.addCommand('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])', 'unselect all rows from top to cursor')
Sheet.addCommand('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])', 'toggle selection of all rows from cursor to bottom')
Sheet.addCommand('gzs', 'select-after', 'select(rows[cursorRowIndex:])', 'select all rows from cursor to bottom')
Sheet.addCommand('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])', 'unselect all rows from cursor to bottom')

Sheet.addCommand('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("select regex: ", type="regex", defaultLast=True), columns="cursorCol"))', 'select rows matching regex in current column')
Sheet.addCommand('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("unselect regex: ", type="regex", defaultLast=True), columns="cursorCol"))', 'unselect rows matching regex in current column')
Sheet.addCommand('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("select regex: ", type="regex", defaultLast=True), columns="visibleCols"))', 'select rows matching regex in any visible column')
Sheet.addCommand('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("unselect regex: ", type="regex", defaultLast=True), columns="visibleCols"))', 'unselect rows matching regex in any visible column')

Sheet.addCommand(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorDisplay: c.getDisplayValue(r) == v), progress=False)', 'select rows matching current cell in current column')
Sheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getDisplayValue(r) == c.getDisplayValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
Sheet.addCommand('z,', 'select-exact-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
Sheet.addCommand('gz,', 'select-exact-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')

Sheet.addCommand('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalExpr(expr, r)), progress=False)', 'select rows matching Python expression in any visible column')
Sheet.addCommand('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalExpr(expr, r)), progress=False)', 'unselect rows matching Python expression in any visible column')

Sheet.addCommand(None, 'select-error-col', 'select(gatherBy(lambda r,c=cursorCol: c.isError(r)), progress=False)', 'select rows with errors in current column')
Sheet.addCommand(None, 'select-error', 'select(gatherBy(lambda r,vcols=visibleCols: isinstance(r, TypedExceptionWrapper) or any([c.isError(r) for c in vcols])), progress=False)', 'select rows with errors in any column')
