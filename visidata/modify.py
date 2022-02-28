from visidata import *

vd.option('color_add_pending', 'green', 'color for rows pending add')
vd.option('color_change_pending', 'reverse yellow', 'color for cells pending modification')
vd.option('color_delete_pending', 'red', 'color for rows pending delete')

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
    BaseSheet.preloadHook(sheet)
    sheet._deferredAdds.clear()
    sheet._deferredMods.clear()
    sheet._deferredDels.clear()

@Sheet.api
def rowAdded(self, row):
    'Mark row as a deferred add-row'
    self._deferredAdds[self.rowid(row)] = row
    def _undoRowAdded(sheet, row):
        if sheet.rowid(row) not in sheet._deferredAdds:
            vd.warning('cannot undo to before commit')
            return
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
                if col.sheet.rowid(row) not in col.sheet._deferredMods:
                    vd.warning('cannot undo to before commit')
                    return
                del col.sheet._deferredMods[col.sheet.rowid(row)]
            else:
                # otherwise, update deferredMods with previous value
                _, rowmods = col.sheet._deferredMods[col.sheet.rowid(row)]
                rowmods[col] = oldval

        vd.addUndo(_undoCellChanged, col, row, oldval)

@Sheet.api
def rowDeleted(self, row):
    'Mark row as a deferred delete-row'
    self._deferredDels[self.rowid(row)] = row
    self.addUndoSelection()
    self.unselectRow(row)
    def _undoRowDeleted(sheet, row):
        if sheet.rowid(row) not in sheet._deferredDels:
            vd.warning('cannot undo to before commit')
            return
        del sheet._deferredDels[sheet.rowid(row)]
    vd.addUndo(_undoRowDeleted, self, row)


@Sheet.api
@asyncthread
def addRows(sheet, rows, index=None, undo=True):
    'Add *rows* after row at *index*.'
    addedRows = {}
    if index is None: index=len(sheet.rows)
    for row in Progress(rows, gerund='adding'):
        addedRows[sheet.rowid(row)] = row
        sheet.addRow(row, index=index+1)

        if sheet.defer:
            sheet.rowAdded(row)
    sheet.setModified()

    @asyncthread
    def _removeRows():
        sheet.deleteBy(lambda r,sheet=sheet,addedRows=addedRows: sheet.rowid(r) in addedRows, commit=True, undo=False)

    if undo:
        vd.addUndo(_removeRows)


@Sheet.api
def deleteBy(sheet, func, commit=False, undo=True):
    '''Delete rows on sheet for which ``func(row)`` returns true.  Return number of rows deleted.
    If sheet.defer is set and *commit* is True, remove rows immediately without deferring.
    If undo is set to True, add an undo for deletion.'''
    oldrows = copy(sheet.rows)
    oldidx = sheet.cursorRowIndex
    ndeleted = 0

    newCursorRow = None   # row to re-place cursor after
    # if commit is True, commit to delete, even if defer is True
    if sheet.defer and not commit:
        ndeleted = 0
        for r in sheet.gatherBy(func, 'deleting'):
            sheet.rowDeleted(r)
            ndeleted += 1
        return ndeleted

    # find next non-deleted row to go to once delete has finished
    while oldidx < len(oldrows):
        if not func(oldrows[oldidx]):
            newCursorRow = sheet.rows[oldidx]
            break
        oldidx += 1

    sheet.rows.clear() # must delete from the existing rows object
    for r in Progress(oldrows, 'deleting'):
        if not func(r):
            sheet.rows.append(r)
            if r is newCursorRow:
                sheet.cursorRowIndex = len(sheet.rows)-1
        else:
            sheet.deleteSourceRow(r)
            ndeleted += 1

    if undo:
        vd.addUndo(setattr, sheet, 'rows', oldrows)
        sheet.setModified()

    if ndeleted:
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
        return (newval is None and curval is not None) or (curval is None and newval is not None) or (col.type(newval) != col.type(curval))
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
    ndeleted = self.deleteBy(self.isDeleted, commit=True, undo=False)

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

    vd.saveSheets(Path(sheet.source), sheet, confirm_overwrite=False)

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

    if sheet.options.confirm_overwrite:
        vd.confirm('really %s? ' % cstr)

    sheet.putChanges()
    sheet.hasBeenModified = False


@Sheet.api
def new_rows(sheet, n):
    return [sheet.newRow() for i in range(n)]

Sheet.addCommand('a', 'add-row', 'addRows([newRow()], index=cursorRowIndex); cursorDown(1)', 'append a blank row')
Sheet.addCommand('ga', 'add-rows', 'n=int(input("add rows: ", value=1)); addRows(new_rows(n), index=cursorRowIndex); cursorDown(1)', 'append N blank rows')
Sheet.addCommand('za', 'addcol-new', 'addColumnAtCursor(SettableColumn(input("column name: "))); cursorRight(1)', 'append an empty column')
Sheet.addCommand('gza', 'addcol-bulk', 'addColumnAtCursor(*(SettableColumn() for c in range(int(input("add columns: "))))); cursorRight(1)', 'append N empty columns')

Sheet.addCommand('z^S', 'commit-sheet', 'commit()', 'commit changes back to source.  not undoable!')
