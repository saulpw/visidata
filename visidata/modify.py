from visidata import *

option('color_add_pending', 'green', 'color for rows pending add')
option('color_change_pending', 'reverse yellow', 'color for cells pending modification')
option('color_delete_pending', 'red', 'color for rows pending delete')

# deferred cached
@Sheet.lazy_property
def _deferredAdds(sheet):
    return dict() # [s.rowid(row)] -> row

@Sheet.lazy_property
def _deferredMods(sheet):
    return dict() # [s.rowid(row)] -> (row, { [col] -> val })

@Sheet.lazy_property
def _deferredDels(sheet):
    return dict() # [s.rowid(row)] -> row

Sheet.colorizers += [
        RowColorizer(9, 'color_add_pending', lambda s,c,r,v: s.rowid(r) in s._deferredAdds),
        CellColorizer(8, 'color_change_pending', lambda s,c,r,v: s.isChanged(c, r)),
        RowColorizer(9, 'color_delete_pending', lambda s,c,r,v: s.isDeleted(r)),
        ]

@Sheet.api
def preloadHook(sheet):
    sheet._deferredAdds.clear()
    sheet._deferredMods.clear()
    sheet._deferredDels.clear()
    # how to call the previous preloadHook? Sheet.preloadHook(sheet)

@Sheet.api
def rowAdded(self, row):
    'Mark row as a deferred add-row'
    self._deferredAdds[self.rowid(row)] = row
    def _undoRowAdded(sheet, row):
        del sheet._deferredAdds[sheet.rowid(row)]
    vd.addUndo(_undoRowAdded, self, row)

@Column.api
def cellChanged(col, row, val):
    'Mark cell at row for col as a deferred edit-cell'
    oldval = col.getValue(row)
    if oldval != val:
        rowid = col.sheet.rowid(row)
        if rowid not in col.sheet._deferredMods:
            rowmods = {}
            col.sheet._deferredMods[rowid] = (row, rowmods)
        else:
            _, rowmods = col.sheet._deferredMods[rowid]
        rowmods[col] = val

        def _undoCellChanged(col, row, oldval):
            if oldval == col.getSourceValue(row):
                # if we have reached the original value, remove from defermods entirely
                del col.sheet._deferredMods[col.sheet.rowid(row)]
            else:
                # otherwise, update deferredMods with previous value
                _, rowmods = col.sheet._deferredMods[rowid]
                rowmods[col] = oldval

        vd.addUndo(_undoCellChanged, col, row, oldval)

@Sheet.api
def rowDeleted(self, row):
    'Mark row as a deferred delete-row'
    self._deferredDels[self.rowid(row)] = row
    def _undoRowDeleted(sheet, row):
        del sheet._deferredDels[sheet.rowid(row)]
    vd.addUndo(_undoRowDeleted, self, row)


@Sheet.api
@asyncthread
def addNewRows(sheet, n, idx):
    'Add *n* new rows after row at *idx*.'
    addedRows = {}
    for i in Progress(range(n), 'adding'):
        row = sheet.newRow()
        addedRows[sheet.rowid(row)] = row
        sheet.addRow(row, idx+1)

        if sheet.defer:
            sheet.rowAdded(row)

    @asyncthread
    def _removeRows():
        sheet.deleteBy(lambda r,sheet=sheet,addedRows=addedRows: sheet.rowid(r) in addedRows, commit=True)

    vd.addUndo(_removeRows)


@Sheet.api
def deleteBy(sheet, func, commit=False):
    'Delete rows on sheet for which ``func(row)`` returns true.  Return number of rows deleted.  If sheet.defer is set and *commit* is True, remove rows immediately without deferring.'
    oldrows = copy(sheet.rows)
    oldidx = sheet.cursorRowIndex
    ndeleted = 0

    row = None   # row to re-place cursor after
    # if commit is True, commit to delete, even if defer is True
    if sheet.defer and not commit:
        ndeleted = 0
        for r in sheet.gatherBy(func, 'deleting'):
            sheet.rowDeleted(r)
            ndeleted += 1
        return ndeleted

    while oldidx < len(oldrows):
        if not func(oldrows[oldidx]):
            row = sheet.rows[oldidx]
            break
        oldidx += 1

    sheet.rows.clear() # must delete from the existing rows object
    for r in Progress(oldrows, 'deleting'):
        if not func(r):
            sheet.rows.append(r)
            if r is row:
                sheet.cursorRowIndex = len(sheet.rows)-1
        else:
            ndeleted += 1

    if not commit:
        vd.addUndo(setattr, sheet, 'rows', oldrows)

    vd.status('deleted %s %s' % (ndeleted, sheet.rowtype))

    return ndeleted


@Sheet.api
def isDeleted(self, row):
    'Return True if *row* has been deferred for deletion.'
    return self.rowid(row) in self._deferredDels

@Sheet.api
def isChanged(self, col, row):
    'Return True if cell at *row* for *col* has been deferred for modification.'
    try:
        row, rowmods = self._deferredMods[self.rowid(row)]
        newval = rowmods[col]
        curval = col.getSourceValue(row)
        return col.type(newval) != col.type(curval)
    except KeyError:
        return False
    except Exception:
        return False

@Column.api
def getSourceValue(col, row):
    'For deferred sheets, return value for *row* in this *col* as it would be in the source, without any deferred modifications applied.'
    return Column.calcValue(col, row)


@Sheet.api
def commitAdds(self):
    'Return the number of rows that have been marked for deferred add-row. Clear the marking.'
    nadded = len(self._deferredAdds.values())
    if nadded:
        vd.status('added %s %s' % (nadded, self.rowtype))
    self._deferredAdds.clear()
    return nadded

@Sheet.api
def commitMods(self):
    'Return the number of modifications (that are not deferred deletes or adds) that been marked for defer mod. Change value to mod for row in col. Clear the marking.'
    nmods = 0
    for row, rowmods in self._deferredMods.values():
        for col, val in rowmods.items():
            try:
                col.putValue(row, val)
                nmods += 1
            except Exception as e:
                vd.exceptionCaught(e)

    self._deferredMods.clear()
    return nmods

@Sheet.api
def commitDeletes(self):
    'Return the number of rows that have been marked for deletion. Delete the rows. Clear the marking.'
    ndeleted = 0

    dest_row = None     # row to re-place cursor after
    oldidx = self.cursorRowIndex
    while oldidx < len(self.rows):
        if not self.isDeleted(self.rows[oldidx]):
            dest_row = self.rows[oldidx]
            break
        oldidx += 1

    newidx = 0
    for r in Progress(list(self.rows), gerund='deleting'):
        if self.isDeleted(self.rows[newidx]):
            self.deleteSourceRow(newidx)
            ndeleted += 1
        else:
            if r is dest_row:
                self.cursorRowIndex = newidx
            newidx += 1

    if ndeleted:
        vd.status('deleted %s %s' % (ndeleted, self.rowtype))
    return ndeleted

@Sheet.api
def deleteSourceRow(sheet, row):
    pass

@asyncthread
@Sheet.api
def putChanges(sheet):
    'Commit changes to ``sheet.source``. May overwrite source completely without confirmation.  Overrideable.'
    sheet.commitAdds()
    sheet.commitMods()
    sheet.commitDeletes()

    saveSheets(Path(sheet.source), sheet, confirm_overwrite=False)

    # clear after save, to ensure cstr (in commit()) is aware of deletes
    sheet._deferredDels.clear()

@Sheet.api
def getDeferredChanges(sheet):
    '''Return changes made to deferred sheets that have not been committed, as a tuple (added_rows, modified_rows, deleted_rows).  *modified_rows* does not include any *added_rows* or *deleted_rows*.

        - *added_rows*: { rowid:row, ... }
        - *modified_rows*: { rowid: (row, { col:val, ... }), ... }
        - *deleted_rows*: { rowid: row }

    *rowid* is from ``Sheet.rowid(row)``. *col* is an actual Column object.
    '''

    # only report mods if they aren't adds or deletes
    mods = {} # [rowid] -> (row, dict(col:val))
    for row, rowmods in sheet._deferredMods.values():
        rowid = sheet.rowid(row)
        if rowid not in sheet._deferredAdds and rowid not in sheet._deferredDels:
            mods[rowid] = (row, {col:val for col, val in rowmods.items() if sheet.isChanged(col, row)})

    return sheet._deferredAdds, mods, sheet._deferredDels

@Sheet.api
def changestr(self, adds, mods, deletes):
    'Return a str for status that outlines how many deferred changes are going to be committed.'
    cstr = ''
    if adds:
        cstr += 'add %d %s' % (len(adds), self.rowtype)

    if mods:
        if cstr: cstr += ' and '
        cstr += 'change %d values' % sum(len(rowmods) for row, rowmods in mods.values())

    if deletes:
        if cstr: cstr += ' and '
        cstr += 'delete %d %s' % (len(deletes), self.rowtype)

    return cstr

@Sheet.api
def commit(sheet, *rows):
    'Commit all deferred changes on this sheet to original ``sheet.source``.'
    if not sheet.defer:
        vd.fail('commit-sheet is not enabled for this sheet type')

    adds, mods, deletes = sheet.getDeferredChanges()
    cstr = sheet.changestr(adds, mods, deletes)
    path = sheet.source

    if not cstr:
        vd.fail('no diffs')

    if options.confirm_overwrite:
        confirm('really %s? ' % cstr)

    sheet.putChanges()

Sheet.addCommand('a', 'add-row', 'addNewRows(1, cursorRowIndex); cursorDown(1)', 'append a blank row')
Sheet.addCommand('ga', 'add-rows', 'addNewRows(int(input("add rows: ", value=1)), cursorRowIndex)', 'append N blank rows')
Sheet.addCommand('za', 'addcol-new', 'addColumnAtCursor(SettableColumn()); cursorRight(1)', 'append an empty column')
Sheet.addCommand('gza', 'addcol-bulk', 'addColumnAtCursor(*(SettableColumn() for c in range(int(input("add columns: ")))))', 'append N empty columns')

Sheet.addCommand('z^S', 'commit-sheet', 'commit()')
