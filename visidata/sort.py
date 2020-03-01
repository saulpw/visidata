from visidata import vd, copy, asyncthread, Progress, exceptionCaught, status, Sheet, options

Sheet.init('_ordering', list, copy=True)  # (col:Column, reverse:bool)


@Sheet.api
def orderBy(sheet, *cols, reverse=False):
    'Add cols to the internal ordering. No cols (or first col None) remove any previous ordering. call sort() if the ordering changes.'
    if options.undo:
        vd.addUndo(setattr, sheet, '_ordering', copy(sheet._ordering))
        if sheet._ordering:
            vd.addUndo(sheet.sort)
        else:
            vd.addUndo(setattr, sheet, 'rows', copy(sheet.rows))

    do_sort = False
    if not cols or cols[0] is None:
        sheet._ordering.clear()
        cols = cols[1:]
        do_sort = True

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

@Sheet.api
@asyncthread
def sort(self):
    'Sort rows according to the current self._ordering.'
    try:
        with Progress(gerund='sorting', total=self.nRows) as prog:
            def sortkey(r):
                ret = []
                for col, reverse in self._ordering:
                    if isinstance(col, str):
                        col = self.column(col)
                    val = col.getTypedValue(r)
                    ret.append(Reversor(val) if reverse else val)

                prog.addProgress(1)
                return ret

            # must not reassign self.rows: use .sort() instead of sorted()
            self.rows.sort(key=sortkey)
    except TypeError as e:
        vd.warning('sort incomplete due to TypeError; change column type')
        vd.exception(e, status=False)


# replace existing sort criteria
Sheet.addCommand('[', 'sort-asc', 'orderBy(None, cursorCol)', 'sort ascending by current column')
Sheet.addCommand(']', 'sort-desc', 'orderBy(None, cursorCol, reverse=True)', 'sort descending by current column')
Sheet.addCommand('g[', 'sort-keys-asc', 'orderBy(None, *keyCols)', 'sort ascending by all key columns')
Sheet.addCommand('g]', 'sort-keys-desc', 'orderBy(None, *keyCols, reverse=True)', 'sort descending by all key columns')

# add to existing sort criteria
Sheet.addCommand('z[', 'sort-asc-add', 'orderBy(cursorCol)')
Sheet.addCommand('z]', 'sort-desc-add', 'orderBy(cursorCol, reverse=True)')
Sheet.addCommand('gz[', 'sort-keys-asc-add', 'orderBy(*keyCols)')
Sheet.addCommand('gz]', 'sort-keys-desc-add', 'orderBy(*keyCols, reverse=True)')
