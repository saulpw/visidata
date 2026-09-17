import itertools

from visidata import vd, VisiData, Sheet, SettableColumn


vd.option('incr_base', 1.0, 'start value for column increments', replay=True)


@VisiData.api
def numrange(vd, n, step=1):
    'Generate n values, starting from options.incr_base and increasing by step for each number.'
    base = type(step)(vd.options.incr_base)
    yield from ((base+x)*step for x in range(n))


def test_numrange(vd=None):
    assert list(vd.numrange(5)) == [1,2,3,4,5]
    assert list(vd.numrange(5, step=5)) == [5,10,15,20,25]  #2769

@VisiData.api
def num(vd, *args):
    'Return parsed string as number, preferring int to float.'
    try:
        return int(*args)
    except Exception:
        return float(*args)


@Sheet.api
def addcol_incr_key(sheet):
    'Add incremental values, restarting whenever the row key changes.'
    base = int(vd.options.incr_base)
    values = [i for _, group in itertools.groupby(sheet.rows, key=sheet.rowkey)
                for i, row in enumerate(group, base)]
    c = SettableColumn(type=int)
    sheet.addColumnAtCursor(c)
    c.setValuesTyped(sheet.rows, *values)


Sheet.addCommand('', 'addcol-incr-key', 'addcol_incr_key()', 'add column with incremental values, restarting at each change in key columns')
Sheet.addCommand('i', 'addcol-incr', 'c=SettableColumn(type=int); addColumnAtCursor(c); c.setValuesTyped(rows, *numrange(nRows))', 'add column with incremental values')
Sheet.addCommand('gi', 'setcol-incr', 'cursorCol.setValuesTyped(selectedRows, *numrange(sheet.nSelectedRows))', 'set current column for selected rows to incremental values')
Sheet.addCommand('zi', 'addcol-incr-step', 'n=num(input("interval step: ")); c=SettableColumn(type=type(n)); addColumnAtCursor(c); c.setValuesTyped(rows, *numrange(nRows, step=n))', 'add column with incremental values times given step')
Sheet.addCommand('gzi', 'setcol-incr-step', 'n=num(input("interval step: ")); cursorCol.setValuesTyped(selectedRows, *numrange(nSelectedRows, n))', 'set current column for selected rows to incremental values times given step')

vd.addMenuItems('''
    Column > Add column > increment > addcol-incr
    Column > Add column > increment by key > addcol-incr-key
    Edit > Modify > selected cells > increment > setcol-incr
''')
