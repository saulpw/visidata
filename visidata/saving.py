from visidata import BaseSheet, Sheet, Column, fail, confirm, CellColorizer, RowColorizer


# deferred cached
Sheet.init('_deferredAdds', dict) # [s.rowid(row)] -> row
Sheet.init('_deferredMods', dict) # [s.rowid(row)] -> val
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
        return col.changed(row)
    except Exception:
        return False


@Sheet.api
def undoMod(self, row):
    for col in self.visibleCols:
        if getattr(col, '_deferredMods', None) and self.rowid(row) in col._deferredMods:
            del col._deferredMods[self.rowid(row)]

    if row in self._deferredDels:
        del self._deferredDels[self.rowid(row)]

    self.restat(row)


@Sheet.api
def markDeleted(self, row):
    if self.defer:
        self._deferredDels[self.rowid(row)] = row
    return row


@Sheet.api
def commit(self, adds, changes, deletes):
    return saveSheets(inputPath("save to: ", value=getDefaultSaveName(self)), self, confirm_overwrite=options.confirm_overwrite)


@Sheet.api
def resetDeferredChanges(self):
    self._deferredMods.clear()
    self._deferredDels.clear()
    self._deferredAdds.clear()


@Sheet.api
def getDeferredChanges(self):
    'Return dict(rowid(row): (row, [changed_cols]))'
    mods = {}  # [rowid] -> (row, [changed_cols])
    for r in list(rows or self.rows):  # copy list because elements may be removed
        if self.rowid(r) not in self._deferredAdds and self.rowid(r) not in self._deferredDels:
            changedcols = [col for col in self.visibleCols if self.changed(col, r)]
            if changedcols:
                mods[self.rowid(r)] = (r, changedcols)

    return self._deferredAdds, mods, self._deferredDels


def changestr(self, adds, changes, deletes):
    cstr = ''
    if adds:
        cstr += 'add %d %s' % (len(adds), self.rowtype)

    if mods:
        if cstr: cstr += ' and '
        cstr += 'change %d values' % sum(len(cols) for row, cols in mods.values())

    if deletes:
        if cstr: cstr += ' and '
        cstr += 'delete %d %s' % (len(deletes), self.rowtype)
    return cstr


@Sheet.api
def save(self, *rows):
    adds, mods, deletes = self.getDeferredChanges()
    cstr = changestr(adds, mods, deletes)
    if options.confirm_overwrite:
        if not cstr:
            warning('no diffs')
        else:
            confirm('really %s? ' % cstr)

    save.commit(dict(adds), mods, dict(deletes))

    self.resetDeferredChanges()

Sheet.addCommand('^S', 'save-sheet', 'save()')
Sheet.addCommand('z^S', 'save-row', 'save(cursorRow)')
Sheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow)')
Sheet.addCommand('gz^R', 'reload-rows', 'for r in self.selectedRows: undoMod(r)')

Sheet.addCommand(None, 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = copy(rows); saveSheets(inputPath("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)')
BaseSheet.addCommand('g^S', 'save-all', 'saveSheets(inputPath("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
