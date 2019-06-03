from visidata import Sheet, Column, fail, confirm, CellColorizer, RowColorizer


# deferred cached
Sheet.init('addedRows', dict) # [s.rowid(row)] -> row
Sheet.init('_modifiedValues', dict) # [s.rowid(row)] -> val
Sheet.init('toBeDeleted', dict) # [s.rowid(row)] -> row

Sheet.init('defer', lambda: True) # set to False for add/delete to take place immediately
Column.init('defer', lambda: True) # set to False to call putValue immediately on set

Sheet.colorizers += [
        CellColorizer(8, 'color_change_pending', lambda s,c,r,v: s.changed(c, r)),
        RowColorizer(9, 'color_delete_pending', lambda s,c,r,v: s.rowid(r) in s.toBeDeleted),
        RowColorizer(9, 'color_add_pending', lambda s,c,r,v: s.rowid(r) in s.addedRows),
    ]


@Sheet.api
def reset(self, *rows):
    self.addedRows.clear()
    self._modifiedValues.clear()
    self.toBeDeleted.clear()


@Sheet.api
def newRow(self):
    row = type(self)._rowtype()
    self.addedRows[self.rowid(row)] = row
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
        if getattr(col, '_modifiedValues', None) and self.rowid(row) in col._modifiedValues:
            del col._modifiedValues[self.rowid(row)]

    if row in self.toBeDeleted:
        del self.toBeDeleted[self.rowid(row)]

    self.restat(row)


@Sheet.api
def markDeleted(self, row):
    if self.defer:
        self.toBeDeleted[self.rowid(row)] = row
    return row

@Sheet.api
def save(self, *rows):
    changes = {}  # [rowid] -> (row, [changed_cols])
    for r in list(rows or self.rows):  # copy list because elements may be removed
        if self.rowid(r) not in self.addedRows and self.rowid(r) not in self.toBeDeleted:
            changedcols = [col for col in self.visibleCols if self.changed(col, r)]
            if changedcols:
                changes[self.rowid(r)] = (r, changedcols)

    if not self.addedRows and not changes and not self.toBeDeleted:
        fail('nothing to save')

    cstr = ''
    if self.addedRows:
        cstr += 'add %d %s' % (len(self.addedRows), self.rowtype)

    if changes:
        if cstr: cstr += ' and '
        cstr += 'change %d values' % sum(len(cols) for row, cols in changes.values())

    if self.toBeDeleted:
        if cstr: cstr += ' and '
        cstr += 'delete %d %s' % (len(self.toBeDeleted), self.rowtype)

    confirm('really %s? ' % cstr)

    self.commit(dict(self.addedRows), changes, dict(self.toBeDeleted))

    self.toBeDeleted.clear()
    self.addedRows.clear()


Sheet.addCommand('^S', 'save-sheet', 'save()')
Sheet.addCommand('z^S', 'save-row', 'save(cursorRow)')
Sheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow)')
Sheet.addCommand('gz^R', 'reload-rows', 'for r in self.selectedRows: undoMod(r)')
