import gc
import weakref

import pytest

import visidata
from visidata import vd


class Row(dict):  # plain dicts cannot be weakly referenced
    pass


def make_sheet(nrows=1000):
    vd.resetVisiData()
    vd._allSheetsSheet = None  # other tests may have replaced vd.allSheets, its source
    vd.push(vd.newSheet('base', 1))
    vs = visidata.PyobjSheet('big', source=[Row(id=i, text='x'*50) for i in range(nrows)])
    vd.push(vs)
    vd.sync()
    vs.options.quitguard  # option lookup in the context of vs
    return vs


def delete_from_sheets_all(vs, longname='delete-row'):
    g = vd.allSheetsSheet
    g.reload()
    vd.push(g)
    if longname == 'delete-row':
        g.cursorRowIndex = vd.allSheets.index(vs)
    else:
        g.selectRow(vs)
    g.execCommand(longname)
    vd.sync()
    vd.remove(g)
    vd.sheets[0].execCommand('go-top')  # deleted sheets are released before the next command


@pytest.mark.usefixtures('curses_setup')
class TestReleaseSheet:
    @pytest.mark.parametrize('before', [None, 'sort-asc', 'select-rows'])
    @pytest.mark.parametrize('delete', ['delete-row', 'delete-selected'])
    def test_sheets_all_delete_frees_sheet(self, before, delete):
        vs = make_sheet()
        if before:
            vs.execCommand(before)
            vd.sync()
        rowref = weakref.ref(vs.rows[0])
        vd.quit(vs)
        assert vs in vd.allSheets

        delete_from_sheets_all(vs, delete)
        assert vs not in vd.allSheets

        ref = weakref.ref(vs)
        del vs
        gc.collect()
        assert ref() is None
        assert rowref() is None

    @pytest.mark.parametrize('before', [None, 'sort-asc', 'select-rows'])
    def test_quit_sheet_free_frees_rows(self, before):
        vs = make_sheet()
        if before:
            vs.execCommand(before)
            vd.sync()
        rowref = weakref.ref(vs.rows[0])
        vs.execCommand('quit-sheet-free')
        vd.sync()
        del vs
        gc.collect()
        assert rowref() is None

    def test_undo_sheets_all_delete(self):
        vs = make_sheet()
        vd.quit(vs)
        g = vd.allSheetsSheet
        g.reload()
        vd.push(g)
        g.execCommand('go-top')  # stands in for the command that opened sheets_all, which undo skips
        g.cursorRowIndex = vd.allSheets.index(vs)
        g.execCommand('delete-row')
        vd.sync()
        assert vs not in vd.allSheets
        g.execCommand('undo-last')  # not released before undo
        vd.sync()
        assert vs in vd.allSheets

    def test_undo_released_sheets_all_delete(self):
        vs = make_sheet()
        vd.quit(vs)
        delete_from_sheets_all(vs)
        assert vs not in vd.allSheets
        delrow = [r for r in vd.cmdlog.rows if r.longname == 'delete-row'][-1]
        assert delrow.undofuncs == [(vd.warning, (f'cannot undo delete-row: sheet "{vs.name}" was released',), {})]

    def test_sheets_all_delete_open_sheet_frees_after_quit(self):
        vs = make_sheet()
        rowref = weakref.ref(vs.rows[0])
        delete_from_sheets_all(vs)  # vs is still on the stack
        assert vs not in vd.allSheets
        assert vs in vd._sheetsToRelease

        vd.quit(vs)
        vd.sheets[0].execCommand('go-top')
        assert vs not in vd._sheetsToRelease

        ref = weakref.ref(vs)
        del vs
        gc.collect()
        assert ref() is None
        assert rowref() is None

    def test_release_keeps_live_sheet(self):
        vs = make_sheet()
        vs.execCommand('sort-asc')
        vd.sync()
        vd.releaseSheet(vs)  # still on the stack: no-op
        assert any(r.undofuncs for r in vs.cmdlog_sheet.rows)

    def test_clipstr_iterator_not_cached(self):
        rows = [Row(id=i) for i in range(3)]
        ref = weakref.ref(rows[0])
        visidata.clipstr(visidata.iterchars(rows), 20)
        vd.clearCaches()  # drawcache on clipstr holds it until the next command
        del rows
        gc.collect()
        assert ref() is None
