import email.message

import pytest

import visidata
from visidata.loaders.eml import EmailSheet


def attachment(filename, payload):
    part = email.message.EmailMessage()
    part.set_content(payload, maintype='application', subtype='octet-stream', filename=filename)
    return part


@pytest.fixture
def sync_exec(monkeypatch):
    monkeypatch.setattr(visidata.vd, 'execAsync', lambda func, *args, **kwargs: func(*args))


@pytest.mark.parametrize('fn', ['../escaped.txt', 'sub/../../escaped.txt', '/tmp/vd-eml-absolute.txt', '..'])
def test_extract_parts_refuses_escaping_filename(tmp_path, sync_exec, fn):
    dest = tmp_path/'extract'/'subdir'
    parts = [attachment('ok.txt', b'ok'), attachment(fn, b'evil')]
    EmailSheet('poc').extract_parts(visidata.Path(str(dest)+'/'), *parts)
    assert (dest/'ok.txt').read_bytes() == b'ok'
    assert not (tmp_path/'extract'/'escaped.txt').exists()
    assert not (tmp_path/'escaped.txt').exists()
    assert not visidata.Path('/tmp/vd-eml-absolute.txt').exists()
