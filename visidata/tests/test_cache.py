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

    def test_type_change_clears_aggregated_totals(self):
        'Changing column type, and undoing that, recomputes aggregate totals.  #3234'
        from visidata import vd, TableSheet, ColumnItem, anytype

        s = TableSheet('t_agg', rows=[['1'], ['2']], columns=[ColumnItem('A', 0, type=anytype)])
        c = s.columns[0]
        agg = vd.aggregators['sum']

        def total():
            c.aggregateTotal(agg)
            vd.sync()
            return c.aggregateTotal(agg)

        assert total() != 3   # sum of strings is an error

        c.type = int
        assert total() == 3

        c._undoType(anytype)  # what undo of type-int calls
        assert total() != 3

    def _sumTotal(self, col):
        from visidata import vd
        agg = vd.aggregators['sum']
        col.aggregateTotal(agg)
        vd.sync()
        return col.aggregateTotal(agg)

    def test_row_and_cell_changes_refresh_aggregated_totals(self):
        'Adding rows, deleting rows, and editing cells recompute aggregate totals.  #3003'
        from visidata import vd
        s, c = self._sheet()
        assert self._sumTotal(c) == 3

        s.addRows([{'a': 10}])
        vd.sync()
        assert self._sumTotal(c) == 13

        s.deleteBy(lambda r: r['a'] == 1)
        assert self._sumTotal(c) == 12

        c.setValue(s.rows[0], 5)
        assert self._sumTotal(c) == 15

    def test_undo_refreshes_aggregated_totals(self):
        'Undoing a row deletion recomputes aggregate totals.  #3003'
        from visidata import vd
        s, c = self._sheet()
        vd.push(s)
        vd.cmdlog.openHook(s, s.source)
        assert self._sumTotal(c) == 3

        s.execCommand('delete-row')
        vd.sync()
        assert self._sumTotal(c) == 2

        s.execCommand('undo-last')
        vd.sync()
        assert self._sumTotal(c) == 3

    def test_late_aggregate_does_not_overwrite_refreshed_totals(self):
        'A total still computing when the cache is reset lands in the discarded cache.  #3234'
        from visidata import vd, INPROGRESS
        s, c = self._sheet()
        agg = vd.aggregators['sum']

        pending = []
        c._aggregateTotalAsync = lambda agg, totals: pending.append(totals)
        assert c.aggregateTotal(agg) is INPROGRESS
        c.recalc()
        pending[0][agg] = 'stale'
        assert c.aggregateTotal(agg) != 'stale'
