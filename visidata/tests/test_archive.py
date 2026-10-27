import gzip
import tarfile

import visidata
from visidata.loaders.archive import TarSheet


def _load(vs):
    vs.reload.__wrapped__(vs)
    return vs


def test_nested_tar_member_csv_gz(tmp_path, monkeypatch):  #3212
    member = tmp_path/'member'
    member.write_bytes(gzip.compress(b'a,b\n1,2\n3,4\n'))
    inner = tmp_path/'inner.tar'
    with tarfile.open(inner, 'w') as tf:
        tf.add(member, arcname='data.csv.gz')
    outer = tmp_path/'outer.tar.gz'
    with tarfile.open(outer, 'w:gz') as tf:
        tf.add(inner, arcname='inner.tar')

    with tarfile.open(inner, 'w') as tf:  # decoy in cwd with the inner tar's name
        tf.add(member, arcname='decoy.csv.gz')
    monkeypatch.chdir(tmp_path)

    ts = _load(TarSheet('outer', source=visidata.Path(str(outer))))
    inner_sheet = _load(ts.openRow(ts.rows[0]))
    assert [r.name for r in inner_sheet.rows] == ['data.csv.gz']

    vs = _load(inner_sheet.openRow(inner_sheet.rows[0]))
    assert [c.name for c in vs.visibleCols] == ['a', 'b']
    assert len(vs.rows) == 2
