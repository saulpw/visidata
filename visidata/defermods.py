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
    self._deferredAdds[self.rowid(row)] = row
    def _undoRowAdded(sheet, row):
        del sheet._deferredAdds[sheet.rowid(row)]
    vd.addUndo(_undoRowAdded, self, row)

@Column.api
def cellChanged(col, row, val):
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
            if oldval == col.getSavedValue(row):
                # if we have reached the original value, remove from defermods entirely
                del col.sheet._deferredMods[col.sheet.rowid(row)]
            else:
                # otherwise, update deferredMods with previous value
                _, rowmods = col.sheet._deferredMods[rowid]
                rowmods[col] = oldval

        vd.addUndo(_undoCellChanged, col, row, oldval)

@Sheet.api
def rowDeleted(self, row):
    self._deferredDels[self.rowid(row)] = row
    def _undoRowDeleted(sheet, row):
        del sheet._deferredDels[sheet.rowid(row)]
    vd.addUndo(_undoRowDeleted, self, row)


@Sheet.api
def isDeleted(self, r):
    return self.rowid(r) in self._deferredDels

@Sheet.api
def isChanged(self, col, row):
    try:
        row, rowmods = self._deferredMods[self.rowid(row)]
        newval = rowmods[col]
        curval = col.getSavedValue(row)
        return col.type(newval) != col.type(curval)
    except KeyError:
        return False
    except Exception:
        return False

@Column.api
def getSavedValue(col, row):
    return Column.calcValue(col, row)


@Sheet.api
def commitAdds(self):
    nadded = len(self._deferredAdds.values())
    if nadded:
        vd.status('added %s %s' % (nadded, self.rowtype))
    self._deferredAdds.clear()
    return nadded

@Sheet.api
def commitMods(self):
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
        status('deleted %s %s' % (ndeleted, self.rowtype))
    return ndeleted

@Sheet.api
def deleteSourceRow(sheet, row):
    pass

@asyncthread
@Sheet.api
def putChanges(sheet):
    'Commit changes to path. adds are a diffset to apply to the last load from or commit to path. By default this overwrites completely, saving as filetype to path, with filetype from path ext.'
    sheet.commitAdds()
    sheet.commitMods()
    sheet.commitDeletes()

    saveSheets(path, sheet, confirm_overwrite=False)

    # clear after save, to ensure cstr (in commit()) is aware of deletes
    sheet._deferredDels.clear()

@Sheet.api
def getDeferredChanges(self):
    'Return adds:dict(rowid:row), mods:dict(rowid:(row, dict(col:val))), dels:dict(rowid: row)'

    # only report mods if they aren't adds or deletes
    mods = {} # [rowid] -> (row, dict(col:val))
    for row, rowmods in self._deferredMods.values():
        rowid = self.rowid(row)
        if rowid not in self._deferredAdds and rowid not in self._deferredDels:
            mods[rowid] = (row, {col:val for col, val in rowmods.items() if self.isChanged(col, row)})

    return self._deferredAdds, mods, self._deferredDels

@Sheet.api
def changestr(self, adds, mods, deletes):
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
    if not sheet.defer:
        fail('commit-sheet is not enabled for this sheet type')

    adds, mods, deletes = sheet.getDeferredChanges()
    cstr = sheet.changestr(adds, mods, deletes)
    path = sheet.source

    if not cstr:
        fail('no diffs')

    if options.confirm_overwrite:
        confirm('really %s? ' % cstr)

    sheet.putChanges()

Sheet.addCommand('z^S', 'commit-sheet', 'commit()')
