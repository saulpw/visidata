import pytest

from visidata import Sheet, ColumnItem


@pytest.mark.usefixtures('curses_setup')
class TestColumnCache:
    def _sheet(self):
        class T(Sheet):
            columns = [ColumnItem('a', 'a')]
            def reload(self):
                self.rows = [{'a': 1}, {'a': 2}]
        s = T('t')
        s.reload()
        return s, s.column('a')

    def test_setValue_invalidates_cache(self):
        'setValue on a cached column must not leave a stale cached value.  #3155'
        s, c = self._sheet()
        c.resetCache()
        assert c.getValue(s.rows[0]) == 1  # populate cache
        c.setValue(s.rows[0], 99, setModified=False)
        assert c.getValue(s.rows[0]) == 99

    def test_undo_reverts_cached_cell(self):
        'Reverting a cell value (as undo does) shows immediately on a cached column.  #3155'
        s, c = self._sheet()
        c.resetCache()
        c.getValue(s.rows[0])                       # prime cache with original
        c.setValue(s.rows[0], 99, setModified=False)  # edit-cell
        assert c.getValue(s.rows[0]) == 99           # redraw repopulates cache
        c.setValue(s.rows[0], 1, setModified=False)  # undo's setValue
        assert c.getValue(s.rows[0]) == 1            # revert visible without another recalc
