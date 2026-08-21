"""
# Usage

Duplicates are determined by the sheet's key columns.

If no key columns are specified, then a duplicate row is one where the values
of *all non-hidden* columns are exactly the same as a row that occurs earlier
in the sheet.

If key columns *are* specified, then duplicates are detected based on the
values in just those columns.

## Commands

- `select-duplicate-rows` sets the selection status in VisiData to `selected`
  for each row in the active sheet that is a duplicate of a prior row.

- `dedupe-rows` pushes a new sheet in which only non-duplicate rows in the
  active sheet are included.
"""


__author__ = "Jeremy Singer-Vine <jsvine@gmail.com>"

from copy import copy

from visidata import Sheet, TableSheet, asyncthread, Progress, vd, ItemColumn


def gen_identify_duplicates(sheet, cols=None):
    """
    Takes a sheet, and returns a generator yielding a tuple for each row
    encountered. The tuple's structure is `(row_object, is_dupe)`, where
    is_dupe is True/False.

    See note in Usage section above regarding how duplicates are determined.
    """

    if not cols:
        keyCols = sheet.keyCols
        cols = None
        if len(keyCols) == 0:
            vd.warning("no key columns specified; using all columns")
            cols = sheet.visibleCols
        else:
            cols = sheet.keyCols

    seen = set()
    seen_unhashable = []  # linear-scan fallback: list/dict values from JSON  #3196
    for r in sheet.rows:
        vals = tuple(col.getValue(r) for col in cols)
        try:
            is_dupe = vals in seen
            if not is_dupe:
                seen.add(vals)
        except TypeError:
            is_dupe = any(vals == existing for existing in seen_unhashable)
            if not is_dupe:
                seen_unhashable.append(vals)
        yield (r, is_dupe)


@Sheet.api
@asyncthread
def select_duplicate_rows(sheet, duplicates=True):
    """
    Given a sheet, sets the selection status in VisiData to `selected` for each
    row that is a duplicate of a prior row.

    If `duplicates = False`, then the behavior is reversed; sets the selection
    status to `selected` for each row that is *not* a duplicate.
    """
    before = len(sheet.selectedRows)

    gen = gen_identify_duplicates(sheet)
    for row, is_dupe in Progress(gen, gerund="selecting", total=sheet.nRows):
        if is_dupe == duplicates:
            sheet.selectRow(row)

    sel_count = len(sheet.selectedRows) - before

    more_str = " more" if before > 0 else ""

    vd.status(f"selected {sel_count}{more_str} {sheet.rowtype}")

@Sheet.api
@asyncthread
def select_col_duplicates(sheet, col, duplicates=True):
    gen = gen_identify_duplicates(sheet, [col])
    for row, is_dupe in Progress(gen, gerund="selecting", total=sheet.nRows):
        if is_dupe == duplicates:
            sheet.selectRow(row)

@Sheet.api
def dedupe_rows(sheet, suffix='_deduped'):
    """
    Given a sheet, pushes a new sheet in which only non-duplicate rows are
    included.
    """
    vs = copy(sheet)
    vs.name += suffix

    @asyncthread
    def _reload(self=vs):
        self.rows = []
        gen = gen_identify_duplicates(sheet)
        prog = Progress(gen, gerund="deduplicating", total=sheet.nRows)
        for row, is_dupe in prog:
            if not is_dupe:
                self.addRow(row)

    vs.reload = _reload
    return vs


# Add longname-commands to VisiData to execute these methods
TableSheet.addCommand(None, "select-col-duplicates", "sheet.select_col_duplicates(cursorCol)", "select each row where the cell in the current column is a duplicate of a prior cell in the current column")
TableSheet.addCommand(None, "select-duplicate-rows", "sheet.select_duplicate_rows()", "select each row that is a duplicate of a prior row")
TableSheet.addCommand(None, "dedupe-rows", "vd.push(sheet.dedupe_rows())", "open new sheet in which only non-duplicate rows in the active sheet are included")

vd.addMenuItems('''
    Row > Select > duplicate rows > select-duplicate-rows
    Data > Deduplicate rows > dedupe-rows
''')

def test_dedupe_unhashable(vd):
    'gen_identify_duplicates must not crash on unhashable typed values  #3196'
    cols = lambda: [ItemColumn('val', 'val')]
    s = Sheet('s', columns=cols(), rows=[
        {'val': [1, 2]},
        {'val': [1, 2]},
        {'val': [3, 4]},
        {'val': 'a'},
        {'val': (1, 2)},
        {'val': 'a'},
        {'val': [1, 2]},
    ])
    assert [is_dupe for row, is_dupe in gen_identify_duplicates(s)] == [False, True, False, False, False, True, True]


"""
# Changelog

## 0.2.0 - 2021-09-22

Use `vd.warning(...)` instead of `warning(...)`

## 0.1.0 - 2020-10-09

Revised for compatibility with VisiData 2.x

## 0.0.1 - 2019-01-01

Internal change, no external effects: Migrates from ._selectedRows to .selectedRows.

## 0.0.0 - 2018-12-30

Initial release.
"""
