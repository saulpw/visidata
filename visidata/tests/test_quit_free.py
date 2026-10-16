import gc
import weakref

import pytest

import visidata
from visidata import vd


class Row(dict):  # plain dicts cannot be weakly referenced
    pass


class BigSheet(visidata.Sheet):
    columns = [visidata.ItemColumn('id', type=int)]
    def iterload(self):
        for i in range(1000):
            yield Row(id=i)


@pytest.mark.usefixtures('curses_setup')
@pytest.mark.parametrize('cmds', [[], ['sort-desc'], ['select-rows']])
def test_quit_sheet_free_frees_rows(cmds):
    vd.resetVisiData()
    vd.push(vd.newSheet('base', 1))
    vs = BigSheet('big', source=None)
    vd.push(vs)
    vd.cmdlog.openHook(vs, vs.source)
    vd.sync()
    for longname in cmds:
        vs.execCommand(longname)
        vd.sync()

    rowref = weakref.ref(vs.rows[0])
    vs.execCommand('quit-sheet-free')
    vd.sync()
    del vs
    gc.collect()
    assert rowref() is None
