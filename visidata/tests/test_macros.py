import json

import pytest

from visidata import vd, BaseSheet


MACRO_VDJ = '{"sheet": "", "col": "", "row": "", "longname": "go-down", "input": "", "keystrokes": "j", "comment": ""}\n'


@pytest.fixture
def macrodir(tmp_path, monkeypatch):
    datadir = tmp_path/'visidata'
    datadir.mkdir()
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    vd.clearCaches()
    vd.options.visidata_dir = str(datadir)
    (datadir/'happy-time.vdj').write_text(MACRO_VDJ)
    (datadir/'macros.jsonl').write_text(json.dumps(dict(binding='happy-time', source='happy-time.vdj', keystroke='Alt+q')) + '\n')
    vd.macrobindings.clear()
    vd.macros.clear()
    vd._macrosheet = None
    vd.reloadMacros()
    yield datadir
    for ks in ('Alt+q', 'Alt+j'):
        if vd.bindkeys._get(ks, BaseSheet):
            BaseSheet.unbindkey(ks)
    if vd.isLongname('happy-time') and 'happy-time' in vd.macrobindings:
        BaseSheet.removeCommand('', 'happy-time')
    vd.macrobindings.clear()
    vd.macrokeys.clear()
    vd._macrosheet = None
    vd.clearCaches()


def boundto(ks):
    return vd.bindkeys._get(ks, BaseSheet)


def macrorow():
    vs = vd.macrosheet
    vs.reload()
    vd.sync()
    return vs, next(r for r in vs.rows if r.binding == 'happy-time')


@pytest.mark.usefixtures('curses_setup')
class TestMacroKeystroke:
    def test_keystroke_from_macros_jsonl(self, macrodir):
        assert boundto('Alt+q') == 'happy-time'

    def test_edit_keystroke_rebinds(self, macrodir):
        vs, row = macrorow()
        vs.column('keystroke').setValue(row, 'Alt+j')
        vs.putChanges()
        vd.sync()
        assert boundto('Alt+j') == 'happy-time'
        assert not boundto('Alt+q')
        saved = [json.loads(L) for L in (macrodir/'macros.jsonl').read_text().splitlines()]
        assert [r['keystroke'] for r in saved if r['binding'] == 'happy-time'] == ['Alt+j']

    def test_clear_keystroke_unbinds(self, macrodir):
        vs, row = macrorow()
        vs.column('keystroke').setValue(row, '')
        vs.putChanges()
        vd.sync()
        assert not boundto('Alt+q')
        assert 'happy-time' in vd.macrobindings

    def test_delete_unbinds(self, macrodir):
        vs, row = macrorow()
        vs.deleteBy(lambda r: r is row)
        vs.putChanges()
        vd.sync()
        assert not boundto('Alt+q')
        assert 'happy-time' not in vd.macrobindings
        assert 'happy-time' not in (macrodir/'macros.jsonl').read_text()
