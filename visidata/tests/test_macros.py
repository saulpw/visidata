import json
import shutil
from pathlib import Path

import pytest

import visidata
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


def cmdrow(longname, input='', col=''):
    return json.dumps(dict(sheet='', col=col, row='', longname=longname, input=input, keystrokes='', comment='')) + '\n'


@pytest.fixture
def replayed(macrodir, monkeypatch):
    'Run a macro made of the given (input, col) rows; return (prompted params, replayed (input, col) rows).'
    prompts = []
    def run(*inputs, braces='', answers={}):
        p = macrodir/'t-macro.vdj'
        p.write_text(''.join(cmdrow('go-down', input=i, col=c) for i, c in inputs))
        vd.setMacro('t-macro', vd.loadMacro(visidata.Path(str(p))), braces=braces)
        vd.sync()
        got = []
        def fakeInputMultiple(**kw):
            prompts.append({k: v.get('value') for k, v in kw.items()})
            return {k: answers.get(k, v.get('value')) for k, v in kw.items()}
        monkeypatch.setattr(vd, 'inputMultiple', fakeInputMultiple, raising=False)
        monkeypatch.setattr(vd, 'replay_sync', lambda cmdlog: got.extend((r.input, r.col) for r in cmdlog.rows), raising=False)
        vd.runMacro('t-macro')
        return prompts, got
    return run


@pytest.mark.usefixtures('curses_setup')
class TestMacroParams:
    def test_input_param_and_default(self, replayed):
        prompts, rows = replayed(('{expr} * {factor=2}', ''), answers=dict(expr='Units'))
        assert prompts == [dict(expr='', factor='2')]
        assert rows == [('Units * 2', '')]

    def test_col_param(self, replayed):
        prompts, rows = replayed(('', '{mycol}'), answers=dict(mycol='Units'))
        assert rows == [('', 'Units')]

    def test_digit_names_not_params(self, replayed):
        prompts, rows = replayed((r'^\d{3}$', ''))
        assert prompts == []
        assert rows == [(r'^\d{3}$', '')]

    def test_escaped_braces(self, replayed):
        prompts, rows = replayed(('f"{{foo}}+{{bar}}" * {n=1}', ''))
        assert prompts == [dict(n='1')]
        assert rows == [('f"{foo}+{bar}" * 1', '')]

    def test_json_input_untouched(self, replayed):
        js = '{"before": "a", "after": {"b": 1}}'
        prompts, rows = replayed((js, ''))
        assert prompts == []
        assert rows == [(js, '')]

    def test_braces_literal(self, replayed):
        prompts, rows = replayed(('f"{foo}+{bar}"', ''), braces='literal')
        assert prompts == []
        assert rows == [('f"{foo}+{bar}"', '')]

    def test_braces_from_macros_jsonl(self, macrodir):
        (macrodir/'t-macro.vdj').write_text(cmdrow('go-down', input='{x}'))
        with (macrodir/'macros.jsonl').open('a') as fp:
            fp.write(json.dumps(dict(binding='t-macro', source='t-macro.vdj', braces='literal')) + '\n')
        vd.reloadMacros()
        assert vd.macrobindings['t-macro'].braces == 'literal'


@pytest.mark.usefixtures('curses_setup')
class TestMacroRecordBraces:
    def record(self, macrodir, monkeypatch, *inputs):
        vd.options.visidata_dir = str(macrodir)
        answers = iter(['t-rec', ''])  # binding, then skip keystroke
        monkeypatch.setattr(vd, 'input', lambda *a, **kw: next(answers), raising=False)
        vd.macroMode = visidata.CommandLogJsonl('current_macro', rows=[])
        for i in inputs:
            vd.macroMode.addRow(visidata.AttrDict(json.loads(cmdrow('go-down', input=i))))
        vd.cmdlog.startMacro()
        vd.sync()
        return [json.loads(L) for L in (macrodir/'macros.jsonl').read_text().splitlines() if 't-rec' in L][0]

    def test_record_with_braces_is_literal(self, macrodir, monkeypatch):
        assert self.record(macrodir, monkeypatch, 'Units', 'f"{foo}"').get('braces') == 'literal'
        assert vd.macrobindings['t-rec'].braces == 'literal'

    def test_record_without_braces_is_param(self, macrodir, monkeypatch):
        assert self.record(macrodir, monkeypatch, 'Units', r'\d{3}', '{"a": 1}').get('braces', '') in ('', 'param', None)

    def test_macrosheet_save_keeps_braces(self, macrodir, monkeypatch):
        self.record(macrodir, monkeypatch, 'f"{foo}"')
        vs, _ = macrorow()
        vs.putChanges()
        vd.sync()
        saved = [json.loads(L) for L in (macrodir/'macros.jsonl').read_text().splitlines()]
        assert [r.get('braces') for r in saved if r['binding'] == 't-rec'] == ['literal']
