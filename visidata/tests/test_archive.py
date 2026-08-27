import gzip
import io
import tarfile
import zipfile

import visidata
from visidata.loaders.archive import TarSheet, ZipSheet


CSV = 'a,b\n1,2\n3,4\n'


def _gzipped(text):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as fp:
        fp.write(text.encode('utf-8'))
    return buf.getvalue()


def _load(vs):
    'Load *vs* synchronously, bypassing the @asyncthread wrapper.'
    vs.reload.__wrapped__(vs)
    return vs


def _archives(tmp_path, membername='data.csv.gz'):
    'Return a .tar.gz and a .zip, each holding *membername* with gzipped CSV.'
    payload = _gzipped(CSV)
    member = tmp_path/'member'
    member.write_bytes(payload)

    tgz = tmp_path/'archive.tar.gz'
    with tarfile.open(tgz, 'w:gz') as tf:
        tf.add(member, arcname=membername)

    zp = tmp_path/'archive.zip'
    with zipfile.ZipFile(zp, 'w') as zf:
        zf.writestr(membername, payload)

    return tgz, zp


def test_stream_path_decompresses_by_suffix():
    # a Path wrapping an already-open stream (which is how archive members are
    # opened) ignored its own compression suffix, handing gzip bytes downstream
    p = visidata.Path('data.csv.gz', fp=io.BytesIO(_gzipped(CSV)))
    assert list(p) == ['a,b', '1,2', '3,4']


def test_stream_path_open_bytes_decompresses():
    p = visidata.Path('data.csv.gz', fp=io.BytesIO(_gzipped(CSV)))
    assert p.open_bytes().read() == CSV.encode('utf-8')


def test_stream_path_read_text_decompresses():
    p = visidata.Path('data.csv.gz', fp=io.BytesIO(_gzipped(CSV)))
    # read_text() hands back the stream contents as-is, so this stays bytes;
    # what matters here is that they are the *decompressed* bytes
    assert p.read_text() == CSV.encode('utf-8')


def test_uncompressed_stream_path_is_untouched():
    p = visidata.Path('data.csv', fp=io.BytesIO(CSV.encode('utf-8')))
    assert list(p) == ['a,b', '1,2', '3,4']


def test_tar_member_csv_gz_opens_as_csv(tmp_path):
    tgz, _ = _archives(tmp_path)
    ts = _load(TarSheet('archive', source=visidata.Path(str(tgz))))
    vs = _load(ts.openRow(ts.rows[0]))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2


def test_zip_member_csv_gz_opens_as_csv(tmp_path):
    _, zp = _archives(tmp_path)
    zs = _load(ZipSheet('archive', source=visidata.Path(str(zp))))
    vs = _load(zs.openRow(zs.rows[0]))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2


def test_tar_open_row_filetype_overrides_unknown_extension(tmp_path):
    # the member's inner extension says nothing useful; the user names the format
    tgz, _ = _archives(tmp_path, membername='data.bin.gz')
    ts = _load(TarSheet('archive', source=visidata.Path(str(tgz))))
    vs = _load(ts.openRow(ts.rows[0], filetype='csv'))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2


def test_zip_open_row_filetype_overrides_unknown_extension(tmp_path):
    _, zp = _archives(tmp_path, membername='data.bin.gz')
    zs = _load(ZipSheet('archive', source=visidata.Path(str(zp))))
    vs = _load(zs.openRow(zs.rows[0], filetype='csv'))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2
