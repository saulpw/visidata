import pickle

import pytest

from visidata import Path, vd

pd = pytest.importorskip('pandas')

called = []


def mark():
    called.append(True)


class Marker:
    def __reduce__(self):
        return (mark, ())


@pytest.fixture
def probe(tmp_path):
    p = tmp_path/'probe.pickle'
    with open(p, 'wb') as fp:
        pickle.dump(Marker(), fp)
    called.clear()
    return Path(p)


def test_pickle_refused_by_default(probe):
    vd.options.pandas_allow_pickle = False
    vs = vd.openPath(probe)
    with pytest.raises(Exception):
        vs.reload.__wrapped__(vs)
    assert not called


def test_pickle_runs_when_allowed(probe):
    vd.options.pandas_allow_pickle = True
    try:
        vs = vd.openPath(probe)
        with pytest.raises(Exception):
            vs.reload.__wrapped__(vs)
        assert called
    finally:
        vd.options.pandas_allow_pickle = False
