import pytest

import visidata

pytest.importorskip('vobject')

from visidata.loaders.vcf import VcfSheet


def _load(tmp_path, name, text):
    p = tmp_path / name
    p.write_bytes(text.encode())
    vs = VcfSheet(name, source=visidata.Path(str(p)))
    vs.reload.__wrapped__(vs)
    return vs


def test_vcf_reads_folded_photo(tmp_path):
    # #3233: a folded PHOTO value (RFC 6350 continuation lines begin with a
    # space) must load; the loader used to insert an extra newline between
    # lines, which broke vobject's line unfolding and halted the loader.
    card = (
        'BEGIN:VCARD\r\n'
        'VERSION:3.0\r\n'
        'FN:Test User\r\n'
        'PHOTO;ENCODING=b:aVBORw0KGgoAAAANSUhEUgAAAUAAAAFACAYAAADNkKWqAAAAAXNSR0IArs\r\n'
        ' 4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGg==\r\n'
        'END:VCARD\r\n'
    )
    vs = _load(tmp_path, 'photo.vcf', card)
    assert len(vs.rows) == 1
    assert {'fn', 'photo'} <= {c.name for c in vs.columns}
