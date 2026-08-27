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


class _Unseekable:
    'A read-only stream with no random access, like an archive piped in on stdin.'
    def __init__(self, b):
        self._fp = io.BytesIO(b)

    def read(self, size=-1):
        return self._fp.read(size)

    def readline(self, size=-1):
        return self._fp.readline(size)

    def close(self):
        return self._fp.close()

    def seekable(self):
        return False


def _held_bytes(vs):
    'Total size of any raw bytes the sheet itself is holding in memory.'
    return sum(len(v) for v in vars(vs).values() if isinstance(v, bytes))


def _nested_tar(tmp_path):
    'Return a .tar.gz holding inner.tar, which holds a gzipped CSV.'
    member = tmp_path/'member'
    member.write_bytes(_gzipped(CSV))

    inner = tmp_path/'inner.tar'
    with tarfile.open(inner, 'w') as tf:
        tf.add(member, arcname='data.csv.gz')

    outer = tmp_path/'outer.tar.gz'
    with tarfile.open(outer, 'w:gz') as tf:
        tf.add(inner, arcname='inner.tar')
    return outer


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


def test_nested_tar_lists_inner_members(tmp_path):
    # a tar inside a tar: the inner TarSheet's source is an open stream, not a
    # pathname that tarfile can reopen from disk
    member = tmp_path/'member'
    member.write_bytes(_gzipped(CSV))

    inner = tmp_path/'inner.tar'
    with tarfile.open(inner, 'w') as tf:
        tf.add(member, arcname='data.csv.gz')

    outer = tmp_path/'outer.tar.gz'
    with tarfile.open(outer, 'w:gz') as tf:
        tf.add(inner, arcname='inner.tar')

    ts = _load(TarSheet('outer', source=visidata.Path(str(outer))))
    inner_sheet = _load(ts.openRow(ts.rows[0]))
    assert [r.name for r in inner_sheet.rows] == ['data.csv.gz']


def test_nested_tar_member_opens(tmp_path):
    member = tmp_path/'member'
    member.write_bytes(_gzipped(CSV))

    inner = tmp_path/'inner.tar'
    with tarfile.open(inner, 'w') as tf:
        tf.add(member, arcname='data.csv.gz')

    outer = tmp_path/'outer.tar.gz'
    with tarfile.open(outer, 'w:gz') as tf:
        tf.add(inner, arcname='inner.tar')

    ts = _load(TarSheet('outer', source=visidata.Path(str(outer))))
    inner_sheet = _load(ts.openRow(ts.rows[0]))
    vs = _load(inner_sheet.openRow(inner_sheet.rows[0]))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2


def test_nested_tar_does_not_buffer_a_seekable_source(tmp_path):
    # the outer archive is on disk, so the inner tar's stream supports random
    # access and can be read in place rather than held in memory
    ts = _load(TarSheet('outer', source=visidata.Path(str(_nested_tar(tmp_path)))))
    inner_sheet = _load(ts.openRow(ts.rows[0]))
    assert [r.name for r in inner_sheet.rows] == ['data.csv.gz']
    assert _held_bytes(inner_sheet) == 0


def test_nested_tar_reads_a_source_that_cannot_seek(tmp_path):
    # regression guard for the buffering fallback: no random access available
    inner = tmp_path/'inner.tar'
    member = tmp_path/'member'
    member.write_bytes(_gzipped(CSV))
    with tarfile.open(inner, 'w') as tf:
        tf.add(member, arcname='data.csv.gz')

    data = inner.read_bytes()
    vs = _load(TarSheet('inner', source=visidata.Path('inner.tar', fp=_Unseekable(data), filesize=len(data))))
    assert [r.name for r in vs.rows] == ['data.csv.gz']


def test_archive_sheets_reuse_one_open_archive(tmp_path):
    # TarSheet.tfp caches its open tarfile for the life of the sheet, the way
    # ZipSheet.zfp has always cached its zipfile
    tgz, zp = _archives(tmp_path)
    ts = _load(TarSheet('t', source=visidata.Path(str(tgz))))
    zs = _load(ZipSheet('z', source=visidata.Path(str(zp))))
    assert ts.tfp is ts.tfp
    assert zs.zfp is zs.zfp
