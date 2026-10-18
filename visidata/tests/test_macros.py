import json
import shutil
from pathlib import Path

import pytest

from visidata import vd, BaseSheet


TEST_DATA_HOME = Path(__file__).parents[2]/'tests/xdg/data'


@pytest.fixture
def macrodir(tmp_path, monkeypatch):
    shutil.copytree(TEST_DATA_HOME, tmp_path, dirs_exist_ok=True)
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    vd.clearCaches()
    vd.reloadMacros()
    yield tmp_path/'visidata'
    for ks in vd.macrokeys.values():
        BaseSheet.unbindkey(ks)
    vd.macrokeys.clear()
    vd.macrobindings.clear()
    vd._macrosheet = None
    vd.clearCaches()


def boundto(ks):
    return vd.bindkeys._get(ks, BaseSheet)


def macrorow():
    vs = vd.macrosheet
    vs.reload()
    vd.sync()
    return vs, next(r for r in vs.rows if r.binding == 'sort-by-col')


@pytest.mark.usefixtures('curses_setup')
class TestMacroKeystroke:
    def test_keystroke_from_macros_jsonl(self, macrodir):
        assert boundto('Alt+q') == 'sort-by-col'

    def test_edit_keystroke_rebinds(self, macrodir):
        vs, row = macrorow()
        vs.column('keystroke').setValue(row, 'Alt+j')
        vs.putChanges()
        vd.sync()
        assert boundto('Alt+j') == 'sort-by-col'
        assert not boundto('Alt+q')
        saved = [json.loads(L) for L in (macrodir/'macros.jsonl').read_text().splitlines()]
        assert [r['keystroke'] for r in saved if r['binding'] == 'sort-by-col'] == ['Alt+j']

    def test_clear_keystroke_unbinds(self, macrodir):
        vs, row = macrorow()
        vs.column('keystroke').setValue(row, '')
        vs.putChanges()
        vd.sync()
        assert not boundto('Alt+q')
        assert 'sort-by-col' in vd.macrobindings

    def test_delete_unbinds(self, macrodir):
        vs, row = macrorow()
        vs.deleteBy(lambda r: r is row)
        vs.putChanges()
        vd.sync()
        assert not boundto('Alt+q')
        assert 'sort-by-col' not in vd.macrobindings
        assert 'sort-by-col' not in (macrodir/'macros.jsonl').read_text()
