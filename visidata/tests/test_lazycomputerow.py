from visidata import Sheet, ItemColumn


def make_sheet():
    vs = Sheet('lcr', columns=[ItemColumn('a', 0), ItemColumn('b', 1)])
    vs.rows = [[1, 2]]
    return vs


def test_currow_reads_cursor_column():
    vs = make_sheet()
    vs.cursorRowIndex = 0
    vs.cursorVisibleColIndex = 0   # cursor on column 'a'

    assert vs.currow.a == 1
    assert vs.currow.as_dict() == {'a': 1, 'b': 2}
