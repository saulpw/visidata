from visidata import *

option('color_add_pending', 'green', 'color for rows pending add')
option('color_delete_pending', 'red', 'color for rows pending delete')

# deferred cached
@Sheet.lazy_property
def _deferredAdds(sheet):
    return dict() # [s.rowid(row)] -> row

@Sheet.lazy_property
def _deferredDels(sheet):
    return dict() # [s.rowid(row)] -> row

Sheet.colorizers += [
        RowColorizer(8, 'color_add_pending', lambda s,c,r,v: s.rowid(r) in s._deferredAdds),
        RowColorizer(9, 'color_delete_pending', lambda s,c,r,v: s.rowid(r) in s._deferredDels),
        ]

@Sheet.api
def _dm_reset(sheet, *rows):
    sheet._deferredAdds.clear()
    sheet._deferredDels.clear()

@BaseSheet.api
def _dm_reload(sheet):
    sheet._dm_reset()
    sheet.reload()

@Sheet.api
def undoMod(self, row):
    # saul: we should integrate this with an undo function
    rowid = self.rowid(row)

    if rowid in self._deferredAds:
        # saul: oes it need to be removed from self.rowid as well?
        del self._deferredAdds[rowid]

    if rowid in self._deferredDels:
        del sel._deferredDels[rowid]

@Sheet.api
def rowAdded(self, row):
    self._deferredAdds[self.rowid(row)] = row

@Sheet.api
def rowDeleted(self, row):
    self._deferredDels[self.rowid(row)] = row


@Sheet.api
def addSourceRow(self, row):
    # saul: unsure about this. what use does this have?
    'Add given row to source. row has already been added to .rows'
    pass

@Sheet.api
def deleteSourceRows(self, row):
    'Delete given row from source. row has already been removed from .rows'
    # saul: unsure about this. what use does this have?
    pass

@Sheet.api
def isDeleted(self, r):
    return self.rowid(r) in self._deferredDels

@Sheet.api
def commitAdds(self):
    nadded = 0
    for row in self._deferredAdds.values():
        try:
            # saul: unsure about this. what use does this have?
            self.addSourceRow(row)
            nadded += 1
        except Exception as e:
            vd.exceptionCaught(e)

    if nadded:
        status('added %s %s' % (nadded, self.rowtype))

    self._deferredAdds.clear()
    return nadded

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
    for r in Progress(self.rows, gerund='deleting'):
        if self.isDeleted(self.rows[newidx]):
            try:
                self.deleteSourceRow(self.rows.pop(newidx))
                ndeleted += 1
            except Exception as e:
                vd.exceptionCaught(e)
        else:
            if r is dest_row:
                self.cursorRowIndex = newidx
            newidx += 1

    if ndeleted:
        status('deleted %s %s' % (ndeleted, self.rowtype))
    return ndeleted

@asyncthread
@Sheet.api
def putChanges(sheet, path, adds, deletes):
    'Commit changes to path. adds are a diffset to apply to the last load from or commit to path. By default this overwrites completely, saving as filetype to path, with filetype from path ext.'
    sheet.commitAdds()
    sheet.commitDeletes()

    saveSheets(path, sheet, confirm_overwrite=False)

    # clear after save, to ensure cstr (in commit()) is aware of deletes
    sheet._deferredDels.clear()

@Sheet.api
def getDeferredChanges(self):
    'Return adds:dict(rowid:row), dels:dict(rowid: row)'
    return self._deferredAdds, self._deferredDels

@Sheet.api
def changestr(self, adds, deletes):
    cstr = ''
    if adds:
        cstr += 'add %d %s' % (len(adds), self.rowtype)

    if deletes:
        if cstr: cstr += ' and '
        cstr += 'delete %d %s' % (len(deletes), self.rowtype)

    return cstr

@Sheet.api
def commit(sheet, *rows):
    if not sheet.defer:
        fail('deferred save is not enabled for this sheet type')

    adds, deletes = sheet.getDeferredChanges()
    cstr = sheet.changestr(adds, deletes)
    path = sheet.source

    if not cstr:
        fail('no diffs')

    if options.confirm_overwrite:
        confirm('really %s? ' % cstr)

    sheet.putChanges(path, adds, {}, deletes)

Sheet.addCommand('z^S', 'commit-sheet', 'commit()')
# saul: reload-sheet needs _dm_reload()
