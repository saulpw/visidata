import os

import pytest

import visidata

pa = pytest.importorskip('pyarrow')


@pytest.mark.parametrize('writer', ['new_stream', 'new_file'])
def test_arrow_from_pipe(writer):  #3184
    t = pa.table({'a': [1, 2], 'b': ['x', 'y']})
    r, w = os.pipe()
    # whole write happens before reading, so this table must fit the pipe buffer (64KB)
    with os.fdopen(w, 'wb') as wf, getattr(pa.ipc, writer)(wf, t.schema) as wr:
        wr.write_table(t)

    vs = visidata.vd.open_arrow(visidata.Path('issue3184.arrow', fp=os.fdopen(r, 'rb')))
    vs.reload.__wrapped__(vs)
    assert [[c.getValue(r) for c in vs.visibleCols] for r in vs.rows] == [[1, 'x'], [2, 'y']]
