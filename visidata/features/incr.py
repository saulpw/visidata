from visidata import VisiData, Sheet, vd


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


Sheet.addCommand('i', 'addcol-incr', 'c=SettableColumn(type=int); addColumnAtCursor(c); c.setValues(rows, *numrange(nRows))', 'add column with incremental values')
Sheet.addCommand('gi', 'setcol-incr', 'cursorCol.setValues(selectedRows, *numrange(sheet.nSelectedRows))', 'set current column for selected rows to incremental values')
Sheet.addCommand('zi', 'addcol-incr-step', 'n=num(input("interval step: ")); c=SettableColumn(type=type(n)); addColumnAtCursor(c); c.setValues(rows, *numrange(nRows, step=n))', 'add column with incremental values times given step')
Sheet.addCommand('gzi', 'setcol-incr-step', 'n=num(input("interval step: ")); cursorCol.setValues(selectedRows, *numrange(nSelectedRows, n))', 'set current column for selected rows to incremental values times given step')

vd.addMenuItems('''
    Column > Add column > increment > addcol-incr
    Edit > Modify > selected cells > increment > setcol-incr
''')
