import locale
import os

import pytest

from visidata import vd, Sheet, ColumnsSheet, ExpectedException, CommandLogJsonl


@pytest.fixture
def env_session(monkeypatch):
    vd.resetVisiData()
    vd.activeCommand = None
    vd.currentReplayRow = None
    setlocale = locale.setlocale
    original_locale = setlocale(locale.LC_ALL)
    for name in ('VD_TEST_ENV', 'LANG', 'LC_ALL', 'LC_NUMERIC'):
        previous = os.environ.get(name)
        monkeypatch.setenv(name, previous or '')
        if previous is None:
            del os.environ[name]
    monkeypatch.setattr(vd, 'scrFull', None)
    yield
    setlocale(locale.LC_ALL, original_locale)
    vd.activeCommand = None
    vd.currentReplayRow = None
    vd.resetVisiData()


def envrows(log):
    return [r for r in log.rows if r.longname == 'set-envvar']


def test_setenv_records_global_and_sheet_logs(env_session):
    first = Sheet('first', rows=[])
    second = Sheet('second', rows=[])
    vd.sheets.extend([first, second])
    first.cmdlog_sheet

    vd.setEnvvar('VD_TEST_ENV', 'a=b')

    assert os.environ['VD_TEST_ENV'] == 'a=b'
    for log in (vd.cmdlog, first.cmdlog_sheet, second.cmdlog_sheet,
                Sheet('later', rows=[]).cmdlog_sheet):
        rows = envrows(log)
        assert len(rows) == 1
        assert not rows[0].sheet
        assert rows[0].input == 'VD_TEST_ENV=a=b'


@pytest.mark.parametrize('initialized', [False, True])
def test_setenv_records_retained_and_shared_logs(env_session, initialized):
    retained = Sheet('retained', rows=[])
    vd.push(retained)
    if initialized:
        retained.cmdlog_sheet
    vd.remove(retained)
    active = Sheet('active', rows=[])
    vd.push(active)
    columns = ColumnsSheet('columns', source=[active])
    vd.push(columns, load=False)

    vd.setEnvvar('VD_TEST_ENV', 'retained')

    assert retained not in vd.sheets
    assert retained in vd.allSheets
    assert columns.cmdlog_sheet is active.cmdlog_sheet
    for log in (vd.cmdlog, retained.cmdlog_sheet, active.cmdlog_sheet):
        rows = envrows(log)
        assert len(rows) == 1
        assert rows[0].input == 'VD_TEST_ENV=retained'
        assert not rows[0].sheet


@pytest.mark.parametrize('value', ['', 'a=b'])
@pytest.mark.parametrize('with_sheet', [False, True])
def test_setenv_replays_once(env_session, value, with_sheet):
    if with_sheet:
        vd.sheets.append(Sheet('data', rows=[]))
    row = vd.cmdlog.newRow(longname='set-envvar', input=f'VD_TEST_ENV={value}')

    assert not vd.replayOne(row)

    assert os.environ['VD_TEST_ENV'] == value
    assert len(envrows(vd.cmdlog)) == 1
    if with_sheet:
        assert len(envrows(vd.activeSheet.cmdlog_sheet)) == 1
    assert not envrows(vd.cmdlog)[0].sheet
    assert envrows(vd.cmdlog)[0].input == f'VD_TEST_ENV={value}'
    assert not vd.lastErrors


@pytest.mark.parametrize('name', ['LANG', 'LC_NUMERIC', 'LC_ALL'])
def test_setenv_refreshes_locale(env_session, name, monkeypatch):
    monkeypatch.delenv('LC_ALL', raising=False)
    monkeypatch.delenv('LC_NUMERIC', raising=False)
    calls = []
    monkeypatch.setattr(vd, 'clearCaches', lambda: calls.append(True))

    vd.setEnvvar(name, 'C')

    assert os.environ[name] == 'C'
    assert locale.setlocale(locale.LC_NUMERIC) == 'C'
    assert calls == [True]


def test_setenv_nonlocale_clears_caches(env_session, monkeypatch):
    calls = []
    monkeypatch.setattr(vd, 'clearCaches', lambda: calls.append(True))
    monkeypatch.setattr(locale, 'setlocale', lambda *args: pytest.fail('unexpected locale change'))

    vd.setEnvvar('VD_TEST_ENV', 'value')

    assert calls == [True]


@pytest.mark.parametrize('previous', [None, 'C'])
def test_setenv_invalid_locale_is_not_recorded(env_session, previous, monkeypatch):
    monkeypatch.delenv('LC_ALL', raising=False)
    if previous is None:
        monkeypatch.delenv('LC_NUMERIC', raising=False)
    else:
        monkeypatch.setenv('LC_NUMERIC', previous)
    original_locale = locale.setlocale(locale.LC_ALL)

    with pytest.raises(ExpectedException):
        vd.setEnvvar('LC_NUMERIC', 'vd_missing_locale')

    assert os.environ.get('LC_NUMERIC') == previous
    assert locale.setlocale(locale.LC_ALL) == original_locale
    assert not envrows(vd.cmdlog)


@pytest.mark.parametrize('assignment', ['VD_TEST_ENV', '=value', 'BAD\x00NAME=value'])
def test_setenv_invalid_assignment_is_not_recorded(env_session, assignment):
    row = vd.cmdlog.newRow(longname='set-envvar', input=assignment)

    assert vd.replayOne(row)
    assert not envrows(vd.cmdlog)


def test_setenv_command_is_recorded_in_macro(env_session, monkeypatch):
    macro = CommandLogJsonl('macro', rows=[])
    monkeypatch.setattr(vd, 'macroMode', macro)
    vd.sheets.append(Sheet('data', rows=[]))
    row = vd.cmdlog.newRow(longname='set-envvar', input='VD_TEST_ENV=macro')

    assert not vd.replayOne(row)

    assert len(envrows(macro)) == 1
    assert len(envrows(vd.cmdlog)) == 1
