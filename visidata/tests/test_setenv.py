import locale
import os

from visidata import vd, Sheet


def envrows(log):
    return [r.input for r in log.rows if r.longname == 'set-envvar']


def test_setenv_replays_from_sheet_cmdlog(monkeypatch):
    vd.resetVisiData()
    monkeypatch.setenv('VD_TEST_ENV', '')
    monkeypatch.delenv('LC_ALL', raising=False)
    monkeypatch.setenv('LC_NUMERIC', '')
    origlocale = locale.setlocale(locale.LC_ALL)
    try:
        vd.setEnvvar('VD_TEST_ENV=a=b')
        vd.setEnvvar('LC_NUMERIC=C')
        assert locale.setlocale(locale.LC_NUMERIC) == 'C'

        vs = Sheet('later', rows=[])
        saved = list(vs.cmdlog.rows)
        assert envrows(vs.cmdlog) == ['VD_TEST_ENV=a=b', 'LC_NUMERIC=C']

        vd.resetVisiData()
        monkeypatch.setenv('VD_TEST_ENV', '')
        for r in saved:
            assert not vd.replayOne(r)
        assert os.environ['VD_TEST_ENV'] == 'a=b'
    finally:
        locale.setlocale(locale.LC_ALL, origlocale)
