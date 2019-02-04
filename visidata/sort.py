from visidata import asyncthread, Progress, exceptionCaught, status, Sheet, undoAttrCopy

undoSort = 'lambda sheet=sheet,oldorder=copy(sheet._ordering),oldrows=copy(sheet.rows): setattr(sheet, "_ordering", oldorder) or setattr(sheet, "rows", oldrows)'

# replace existing sort criteria
Sheet.addCommand('[', 'sort-asc', 'orderBy(None, cursorCol)', undo=undoSort),
Sheet.addCommand(']', 'sort-desc', 'orderBy(None, cursorCol, reverse=True)', undo=undoSort),
Sheet.addCommand('g[', 'sort-keys-asc', 'orderBy(None, *keyCols)', undo=undoSort),
Sheet.addCommand('g]', 'sort-keys-desc', 'orderBy(None, *keyCols, reverse=True)', undo=undoSort),

# add to existing sort criteria
Sheet.addCommand('z[', 'sort-asc-add', 'orderBy(cursorCol)', undo=undoSort),
Sheet.addCommand('z]', 'sort-desc-add', 'orderBy(cursorCol, reverse=True)', undo=undoSort),
Sheet.addCommand('gz[', 'sort-keys-asc-add', 'orderBy(*keyCols)', undo=undoSort),
Sheet.addCommand('gz]', 'sort-keys-desc-add', 'orderBy(*keyCols, reverse=True)', undo=undoSort),

Sheet.init('_ordering', list, copy=True)  # (cols, reverse:bool)

@Sheet.api
def orderBy(self, *cols, reverse=False):
    'Add cols to the internal ordering. No cols (or first col None) remove any previous ordering. call sort() if the ordering changes.'
    do_sort = False
    if not cols or cols[0] is None:
        self._ordering.clear()
        cols = cols[1:]
        do_sort = True

    if cols:
        self._ordering.append((cols, reverse))
        do_sort = True

    if do_sort:
        self.sort()

@Sheet.api
@asyncthread
def sort(self):
    'Sort rows according to the current self._ordering.'
    try:
        with Progress(gerund='sorting', total=len(self.rows)*len(self._ordering)) as prog:
            for cols, reverse in self._ordering[::-1]:
                def sortkey(r):
                    prog.addProgress(1)
                    return tuple(c.getTypedValue(r) for c in cols)

                # must not reassign self.rows: use .sort() instead of sorted()
                self.rows.sort(key=sortkey, reverse=reverse)
    except TypeError as e:
        status('sort incomplete due to TypeError; change column type')
        exceptionCaught(e, status=False)
