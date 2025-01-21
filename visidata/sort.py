from copy import copy
from visidata import vd, asyncthread, Progress, Sheet, options, UNLOADED

@Sheet.api
def orderBy(sheet, *cols, reverse=False, change_column=False):
    '''Add *cols* to internal ordering and re-sort the rows accordingly.
    Pass *reverse* as True to order these *cols* descending.
    Pass empty *cols* (or cols[0] of None) to clear internal ordering.
    Set *change_column* to True to change the sort status of a single column: add/remove/invert it.
    *cols* must have length 1. Sort columns that had higher priority are unchanged. Lower-priority columns are removed.
    If *change_column* is False, *cols* will add to the existing ordering columns.'''

    if options.undo:
        vd.addUndo(setattr, sheet, '_ordering', copy(sheet._ordering))
        vd.addUndo(setattr, sheet, 'rows', copy(sheet.rows))

    do_sort = False
    if not cols or cols[0] is None:
        sheet._ordering.clear()
        cols = cols[1:]
        do_sort = True

    if change_column:
        if len(cols) > 1:
            vd.fail('sort order edit must only be applied to a single column')
        new_ordering = edit_ordering(sheet._ordering, cols[0], reverse)
        sheet._ordering = new_ordering
        do_sort = True
    else:
        for c in cols:
            sheet._ordering.append((c, reverse))
            do_sort = True

    if do_sort:
        sheet.sort()

class Reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj


def edit_ordering(ordering, col, reverse):
    '''Return a modified ordering based on editing a single column *col*:   add it, remove it, or flip its direction.
    Columns after *col* in the ordering (with lower sort priority) are also removed from the ordering.
    *ordering* is a list of tuples:  (Column, boolean), where the boolean defines the sort direction.
    '''
    new_ordering = []
    # handle changes to status of columns that are already in the ordering:  add/remove/flip
    changed = False
    for c, old_reverse in ordering:
        if c == col:
            if reverse != old_reverse: # reverse the column's sort direction
                new_ordering.append((c, reverse))
            # if the sort direction is unchanged, remove the column from the ordering
            changed = True
            # columns after the edited column will be dropped from the ordering
            break
        new_ordering.append((c, old_reverse))
    if not changed:
        new_ordering.append((col, reverse))
    return new_ordering

@Sheet.cached_property
def ordering(sheet) -> 'list[tuple[Column, bool]]':
    ret = []
    for col, reverse in sheet._ordering:
        if isinstance(col, str):
            col = sheet.column(col)
        ret.append((col, reverse))
    return ret


@Sheet.api
def sortkey(sheet, r, ordering:'list[tuple[Column, bool]]'=[]):
    ret = []
    for col, reverse in (ordering or sheet.ordering):
        val = col.getTypedValue(r)
        ret.append(Reversor(val) if reverse else val)

    return ret


@Sheet.api
@asyncthread
def sort(self):
    'Sort rows according to the current internal ordering.'
    if self.rows is UNLOADED:
        return
    try:
        with Progress(gerund='sorting', total=self.nRows) as prog:
            # replace ambiguous colname strings with unambiguous Column objects  #2494
            self._ordering = self.ordering
            def _sortkey(r):
                prog.addProgress(1)
                return self.sortkey(r, ordering=self._ordering)

            # must not reassign self.rows: use .sort() instead of sorted()
            self.rows.sort(key=_sortkey)
    except TypeError as e:
        vd.warning('sort incomplete due to TypeError; change column type')
        vd.exceptionCaught(e, status=False)


# replace existing sort criteria
Sheet.addCommand('[', 'sort-asc', 'orderBy(None, cursorCol)', 'sort ascending by current column; replace any existing sort criteria')
Sheet.addCommand(']', 'sort-desc', 'orderBy(None, cursorCol, reverse=True)', 'sort descending by current column; replace any existing sort criteria ')
Sheet.addCommand('g[', 'sort-keys-asc', 'orderBy(None, *keyCols)', 'sort ascending by all key columns; replace any existing sort criteria')
Sheet.addCommand('g]', 'sort-keys-desc', 'orderBy(None, *keyCols, reverse=True)', 'sort descending by all key columns; replace any existing sort criteria')

# add to existing sort criteria
Sheet.addCommand('', 'sort-asc-add', 'orderBy(cursorCol)', 'sort ascending by current column; add to existing sort criteria')
Sheet.addCommand('', 'sort-desc-add', 'orderBy(cursorCol, reverse=True)', 'sort descending by current column; add to existing sort criteria')
Sheet.addCommand('z[', 'sort-asc-change', 'orderBy(cursorCol, change_column=True)', 'sort ascending by current column; keep higher priority sort criteria')
Sheet.addCommand('z]', 'sort-desc-change', 'orderBy(cursorCol, reverse=True, change_column=True)', 'sort descending by current column; keep higher priority sort criteria')
Sheet.addCommand('gz[', 'sort-keys-asc-add', 'orderBy(*keyCols)', 'sort ascending by all key columns; add to existing sort criteria')
Sheet.addCommand('gz]', 'sort-keys-desc-add', 'orderBy(*keyCols, reverse=True)', 'sort descending by all key columns; add to existing sort criteria')

vd.addMenuItems('''
    Column > Sort by > current column only > ascending > sort-asc
    Column > Sort by > current column only > descending > sort-desc
    Column > Sort by > current column also > ascending > sort-asc-add
    Column > Sort by > current column also > descending > sort-desc-add
    Column > Sort by > key columns > ascending > sort-keys-asc
    Column > Sort by > key columns > descending > sort-keys-desc
''')
