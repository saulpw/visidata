from copy import copy
from visidata import vd, Sheet, Progress, asyncthread, options, UNLOADED

@Sheet.api
@asyncthread
def sortSelected(self, ordering):
    """sort the rows that are selected, in place so that each originally-selected row takes the place of another.
    *ordering* is a list of tuples: (col_name_str, reverse_sort_bool) (string and bool)"""
    if self.rows is UNLOADED or not self.rows:
        return
    if self.nSelectedRows == 0:
        vd.fail('no rows selected')
        return

    if options.undo:
        vd.status('undo added')
        vd.addUndo(setattr, self, 'rows', copy(self.rows))

# temporary:  save data to test integrity after the sort
    rows_initial = { self.rowid(r) for r in self.rows }
    selected_initial = set(self._selectedRows.keys())

    with Progress(gerund='sorting', total=self.nSelectedRows) as prog:
        selected = list(self._selectedRows.values())
        selected_rowids = set(self._selectedRows.keys())

        selected_indices = []
        for i, r in enumerate(self.rows):
            rowid = self.rowid(r)
            if rowid in selected_rowids:
                selected_indices.append(i)
                selected_rowids.remove(rowid)
            if len(selected_rowids) == 0:
                break
        try:
            def _sortkey(r):
                prog.addProgress(1)
                return self.sortkey(r, ordering=ordering)
            sorted_selected = sorted(selected, key=_sortkey)
        except TypeError as e:
            vd.warning('sort incomplete due to TypeError; change column type')
            vd.exceptionCaught(e, status=False)
            return
        for selected_idx, r in zip(selected_indices, sorted_selected, strict=True):
            self.rows[selected_idx] = r

# temporary:  make sure we haven't lost any rows in the sheet or the selection
    rows_final = { self.rowid(r) for r in self.rows }
    selected_final = set(self._selectedRows.keys())
    assert(rows_initial == rows_final)
    assert(selected_initial == selected_final)

Sheet.addCommand(None, 'sort-selected-asc', 'sortSelected([(cursorCol, False)])', 'sort selected rows by the current column, in ascending order')
Sheet.addCommand(None, 'sort-selected-desc', 'sortSelected([(cursorCol, True)])', 'sort selected rows by the current column, in descending order')
