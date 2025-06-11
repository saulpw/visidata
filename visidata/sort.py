from copy import copy
from visidata import vd, asyncthread, Progress, Sheet, Column, options, UNLOADED, ColumnsSheet
import re

cmdlog_col_prefix='\u241f'  #string ␟ to mark the start of column info in an ordering string

@Sheet.api
def orderBy(sheet, *cols, reverse=False, change_column=False, save_cmd_input=True):
    '''Add *cols* to internal ordering and re-sort the rows accordingly.
    Pass *reverse* as True to order these *cols* descending.
    Pass empty *cols* (or cols[0] of None) to clear internal ordering.
    Set *change_column* to True to change the sort status of a single column: add/remove/invert it.
    When changing a column, *cols* must have length 1. Sort columns that had higher priority are unchanged. Lower-priority columns are removed.
    If *change_column* is False, *cols* will be added to the existing ordering.
    If *save_cmd_input* is True, the full ordering that results will be saved in the cmdlog for future replay in the 'input' parameter.
    '''

    if options.undo:
        vd.addUndo(setattr, sheet, '_ordering', copy(sheet._ordering))
        vd.addUndo(setattr, sheet, 'rows', copy(sheet.rows))

    # for replay, read the full column ordering from the cmdlog input parameter  #2688
    input = vd.getLastArgs()
    if input:
        sheet._ordering = order_from_string(sheet, input)
        sheet.sort()
        if save_cmd_input:
            vd.activeCommand.input = order_string(sheet)
        return

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
    if save_cmd_input:
        vd.activeCommand.input = order_string(sheet)

class Reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj

def order_string(sheet):
    sheet._ordering = sheet.ordering  #converts any ambiguous colname strings to unambiguous Column objects
    ret = ''.join([cmdlog_col_prefix+('>' if reverse else '<') + str(col.name) for col, reverse in sheet._ordering])
    return ret

def order_from_string(sheet, s):
    instructions = re.split(cmdlog_col_prefix + '(?=[<>])', s)[1:]
    ordering = []
    for instr in instructions:
        c = sheet.column(instr[1:])
        if instr[0] == '<':
            reverse = False
        elif instr[0] == '>':
            reverse = True
        ordering.append((c, reverse))
    return ordering

def edit_ordering(ordering, col, reverse):
    '''Return a modified ordering based on editing a single column *col*:   add it, remove it, or flip its direction.
    Columns after *col* in the ordering (with lower sort priority) are also removed from the ordering.
    *ordering* is a list of tuples:  (Column, boolean), where the boolean defines the sort direction.
    '''
    new_ordering = []
    # handle changes to status of columns that are already in the ordering:  add/remove/flip
    changed = False
    for c, old_reverse in ordering:
        if c is col:
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

ColumnsSheet.columns += [
        Column('sortorder',
            type=int,
            getter=lambda c,r: _sort_order(c, r),
            help='sort priority and direction in source sheet')
]

def _sort_order(col, srccol):
    sort_cols = [(n+1, reverse) for n, (c, reverse) in enumerate(srccol.sheet.ordering) if c is srccol]
    if not sort_cols:
        return None
    n, reverse = sort_cols[0]
    return -n if reverse else n


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
