from visidata import BaseSheet, Sheet, Column, fail, confirm, CellColorizer, RowColorizer, asyncthread, options, saveSheets, inputPath, getDefaultSaveName, warning, status, Path, copy, Progress, option


option('color_add_pending', 'green', 'color for rows pending add')
option('color_change_pending', 'reverse yellow', 'color for cells pending modification')
option('color_delete_pending', 'red', 'color for rows pending delete')


# deferred cached
Sheet.init('_deferredAdds', dict) # [s.rowid(row)] -> row
Sheet.init('_deferredMods', dict) # [s.rowid(row)] -> (row, { [col] -> val })
Sheet.init('_deferredDels', dict) # [s.rowid(row)] -> row

Sheet.colorizers += [
        CellColorizer(8, 'color_change_pending', lambda s,c,r,v: s.changed(c, r)),
        RowColorizer(9, 'color_delete_pending', lambda s,c,r,v: s.rowid(r) in s._deferredDels),
        RowColorizer(9, 'color_add_pending', lambda s,c,r,v: s.rowid(r) in s._deferredAdds),
    ]


@Sheet.api
def reset(self, *rows):
    self._deferredAdds.clear()
    self._deferredMods.clear()
    self._deferredDels.clear()


@Sheet.api
def newRow(self):
    row = type(self)._rowtype()
    self._deferredAdds[self.rowid(row)] = row
    return row


@Sheet.api
def changed(self, col, row):
    try:
        row, rowmods = self._deferredMods[self.rowid(row)]
        newval = rowmods[col]
        curval = col.calcValue(row)
        return col.type(newval) != col.type(curval)
    except KeyError:
        return False
    except Exception:
        return False


@Sheet.api
def undoMod(self, row):
    rowid = self.rowid(row)

    if rowid in self._deferredMods:
        del col._deferredMods[rowid]

    if rowid in self._deferredDels:
        del self._deferredDels[rowid]

    if rowid in self._deferredAdds:
        del self._deferredAdds[rowid]


@Sheet.api
def deleteBy(self, func):
    'Delete rows for which func(row) is true.  Returns number of deleted rows.'
    for i, r in enumerate(Progress(self.rows, 'deleting')):
        if not func(r):
            self.markDeleted(r)

    if not self.defer:
        self.commitDeletes()


@Sheet.api
def deleteRows(self, rows):
    for r in rows:
        self.markDeleted(r)

    if not self.defer:
        self.commitDeletes()


@Sheet.api
def addSourceRow(self, row):
    'Add given row to source. row has already been added to .rows'
    pass


@Sheet.api
def deleteSourceRow(self, row):
    'Delete given row from source. row has already been removed from .rows'
    pass


@Sheet.api
def commitAdds(self):
    nadded = 0
    for row in self._deferredAdds.values():
        try:
            self.addSourceRow(row)
            nadded += 1
        except Exception as e:
            exceptionCaught(e)

    if nadded:
        status('added %s %s' % (nadded, self.rowtype))

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
                exceptionCaught(e)

    self._deferredMods.clear()
    return nmods


@Sheet.api
def isDeleted(self, r):
    return self.rowid(r) in self._deferredDels


@Sheet.api
def commitDeletes(self):
    ndeleted = 0

    dest_row = None   # row to re-place cursor after
    oldidx = self.cursorRowIndex
    while oldidx < len(self.rows):
        if not self.isDeleted(self.rows[oldidx]):
            dest_row = self.rows[oldidx]
            break
        oldidx += 1

    newidx = 0
    for r in Progress(self.rows, gerund='deleting'):
        if self.isDeleted(self.rows[oldidx]):
            try:
                self.deleteSourceRow(rows.pop(newidx))
                ndeleted += 1
            except Exception as e:
                exceptionCaught(e)
        else:
            if r is dest_row:
                self.cursorRowIndex = newidx
            newidx += 1

    self._deferredDels.clear()
    if ndeleted:
        status('deleted %s %s' % (ndeleted, self.rowtype))
    return ndeleted


@asyncthread
@Sheet.api
def commit(self, path, adds, changes, deletes):
    'Commit changes to path.  adds/changes/deletes are a diffset to apply to the last load from or commit to path.  By default this overwrites completely, saving as filetype to path, with filetype from path ext.'
    if not self.savesToSource:
        saveSheets(path, self, confirm_overwrite=options.confirm_overwrite)
    else:
        self.commitAdds()
        self.commitMods()
        self.commitDeletes()


@Sheet.api
def getDeferredChanges(self):
    'Return adds:dict(rowid:row), mods:dict(rowid:(row, dict(col:val))), dels:dict(rowid:row)'

    # only report mods if they aren't adds or deletes
    mods = {}  # [rowid] -> (row, dict(col:val))
    for row, rowmods in self._deferredMods.values():
        rowid = self.rowid(row)
        if rowid not in self._deferredAdds and rowid not in self._deferredDels:
            mods[rowid] = (row, {col:val for col, val in rowmods.items() if self.changed(col, row)})

    return self._deferredAdds, mods, self._deferredDels


@Sheet.api
def markDeleted(self, row, mark=True):
    if mark:
        self._deferredDels[self.rowid(row)] = row
    else:
        del self._deferredDels[self.rowid(row)]
    return row


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
def save(sheet, *rows):
    adds, mods, deletes = sheet.getDeferredChanges()
    cstr = sheet.changestr(adds, mods, deletes)
    savingToSource = sheet.savesToSource
    confirm_overwrite = options.confirm_overwrite
    if not cstr and savingToSource:
        fail('no diffs')

    if savingToSource:
        if isinstance(sheet.source, Path):
            path = sheet.source
        else:
            path = None
    else:
        path = inputPath("save to: ", value=getDefaultSaveName(sheet))
        if str(path) == str(sheet.source):
            savingToSource = True

    if confirm_overwrite and savingToSource:
        confirm('really %s? ' % cstr)

    elif not savingToSource and path.exists() and confirm_overwrite:
        confirm("%s already exists. overwrite? " % path.given)

    sheet.commit(path, adds, mods, deletes)


Sheet.addCommand('^S', 'save-sheet', 'save()')
Sheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow)')
Sheet.addCommand('gz^R', 'reload-rows', 'for r in self.selectedRows: undoMod(r)')

Sheet.addCommand(None, 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = copy(rows); saveSheets(inputPath("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)')
BaseSheet.addCommand('g^S', 'save-all', 'saveSheets(inputPath("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
