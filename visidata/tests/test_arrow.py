import os

import pytest

import visidata

pa = pytest.importorskip('pyarrow')


def _table():
    return pa.table({'a': [1, 2], 'b': ['x', 'y']})


def _load(vs):
    vs.reload.__wrapped__(vs)
    return [[c.getValue(r) for c in vs.visibleCols] for r in vs.rows]


def test_arrows_stream_from_pipe():
    # #3184: the IPC streaming format must load from a non-seekable,
    # non-reopenable source, like the stdin pipe of `vd -f arrows -`.
    r, w = os.pipe()
    with os.fdopen(w, 'wb') as wf, pa.ipc.new_stream(wf, _table().schema) as writer:
        writer.write_table(_table())

    p = visidata.Path('demo.arrows', fp=os.fdopen(r, 'rb'))
    assert _load(visidata.vd.open_arrows(p)) == [[1, 'x'], [2, 'y']]


def test_arrow_file_from_disk(tmp_path):
    f = str(tmp_path / 'demo.arrow')
    with pa.ipc.new_file(f, _table().schema) as writer:
        writer.write_table(_table())

    assert _load(visidata.vd.open_arrow(visidata.Path(f))) == [[1, 'x'], [2, 'y']]


def test_arrow_filetype_sniffs_stream_format_on_disk(tmp_path):
    # a stream-format file opened with `-f arrow` still loads, by falling
    # back to the stream reader (files, unlike pipes, can be reopened).
    f = str(tmp_path / 'demo.arrow')
    with pa.ipc.new_stream(f, _table().schema) as writer:
        writer.write_table(_table())

    assert _load(visidata.vd.open_arrow(visidata.Path(f))) == [[1, 'x'], [2, 'y']]
