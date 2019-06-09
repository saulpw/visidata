from visidata import BaseSheet, Sheet, Column, fail, confirm, CellColorizer, RowColorizer, asyncthread, options, saveSheets, inputPath, getDefaultSaveName, warning, status, Path


# deferred cached
Sheet.init('_deferredAdds', dict) # [s.rowid(row)] -> row
Sheet.init('_deferredMods', dict) # [s.rowid(row)] -> (row, { [col] -> val })
Sheet.init('_deferredDels', dict) # [s.rowid(row)] -> row

Sheet.init('defer', lambda: True) # set to False for add/delete to take place immediately
Column.init('defer', lambda: True) # set to False to call putValue immediately on set

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
    oldrows = copy(self.rows)
    oldidx = self.cursorRowIndex
    ndeleted = 0

    row = None   # row to re-place cursor after
    while oldidx < len(oldrows):
        if not func(oldrows[oldidx]):
            row = self.rows[oldidx]
            break
        oldidx += 1

    self.rows.clear()
    for r in Progress(oldrows, 'deleting'):
        if not func(r):
            self.rows.append(r)  # NOT addRow
            if r is row:
                self.cursorRowIndex = len(self.rows)-1
        else:
            self.deleteRows([r])
            ndeleted += 1

    status('deleted %s %s' % (ndeleted, self.rowtype))
    return ndeleted


@Sheet.api
@asyncthread
def deleteRows(self, rows):
    for row in rows:
        self._deferredDels[self.rowid(row)] = row

    if self.sheet.defer:
        return

    self.deleteBy(lambda r,self=self,dels=self._deferredDels: self.rowid(r) in dels)


@asyncthread
@Sheet.api
def commit(sheet, path, adds, changes, deletes):
    saveSheets(path, sheet, confirm_overwrite=options.confirm_overwrite)
    for row, rowmods in sheet._deferredMods.values():
        for col, val in rowmods.items():
            col.putValue(row, val)

    sheet.resetDeferredChanges()


@Sheet.api
def resetDeferredChanges(self):
    self._deferredMods.clear()
    self._deferredDels.clear()
    self._deferredAdds.clear()


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
    if not cstr:
        warning('no diffs')
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

    elif not savingToSource and path.exists():
        confirm("%s already exists. overwrite? " % path.fqpn)

    sheet.commit(path, adds, mods, deletes)


Sheet.addCommand('^S', 'save-sheet', 'save()')
Sheet.addCommand('z^S', 'save-row', 'save(cursorRow)')
Sheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow)')
Sheet.addCommand('gz^R', 'reload-rows', 'for r in self.selectedRows: undoMod(r)')

Sheet.addCommand(None, 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = copy(rows); saveSheets(inputPath("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)')
BaseSheet.addCommand('g^S', 'save-all', 'saveSheets(inputPath("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
