import pytest

from visidata import Column, Sheet, vd


@pytest.mark.usefixtures('curses_setup')
class TestAllColumnsSheet:
    def _sheet(self, name, *colnames):
        vs = Sheet(name, columns=[Column(n) for n in colnames])
        vs.rows = [{}]
        vs.recalc()
        vs.pane = 1
        return vs

    def test_columns_all_picks_up_sheets_opened_later(self):
        'gC must list columns from sheets opened after the first columns-all.  #3191'
        old_sheets = list(vd.sheets)
        old_cached = vd._allColumnsSheet
        try:
            vd.sheets[:] = []
            vd._allColumnsSheet = None

            s1 = self._sheet('data1', 'Key', 'A', 'B')
            vd.sheets[:] = [s1]

            vs = vd.allColumnsSheet
            vs.source = vd.stackedSheets
            vs.loader()
            assert [c.name for c in vs.rows] == ['Key', 'A', 'B']
            assert vs.columns[0].hidden  # single source hides the sheet column

            s2 = self._sheet('data2', 'Key', 'C', 'D')
            vd.sheets[:] = [s1, s2]

            # same cached sheet object the command reuses
            vs = vd.allColumnsSheet
            vs.source = vd.stackedSheets
            vs.loader()

            names = [(c.sheet.name, c.name) for c in vs.rows]
            assert names == [
                ('data1', 'Key'), ('data1', 'A'), ('data1', 'B'),
                ('data2', 'Key'), ('data2', 'C'), ('data2', 'D'),
            ]
            assert not vs.columns[0].hidden  # sheet column distinguishes sources
        finally:
            vd.sheets[:] = old_sheets
            vd._allColumnsSheet = old_cached
