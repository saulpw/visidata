import io
import pathlib
from types import SimpleNamespace

import pytest

from visidata.loaders import unzip_http


def fake_rzf(contents):
    rzf = unzip_http.RemoteZipFile.__new__(unzip_http.RemoteZipFile)
    rzf.open = lambda fn: io.BytesIO(contents)
    return rzf


@pytest.mark.parametrize('member', ['../escaped.txt', '/tmp/absolute.txt', 'sub/../../escaped.txt'])
def test_extract_refuses_escaping_member(tmp_path, member):
    target = tmp_path/'target'
    target.mkdir()
    with pytest.raises(Exception, match='unsafe path'):
        fake_rzf(b'x').extract(member, path=target)
    assert list(tmp_path.rglob('*')) == [target]


def test_extract_writes_inside_target(tmp_path):
    fake_rzf(b'hello').extract('sub/ok.txt', path=tmp_path)
    assert (tmp_path/'sub'/'ok.txt').read_bytes() == b'hello'


def test_cli_full_filepaths_refuses_escaping_member(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(unzip_http, 'extract_one', lambda outfile, rzf, f, ofname: outfile.write(b'x'))
    f = SimpleNamespace(filename='../escaped.txt', compress_size=1)
    args = SimpleNamespace(files=['*'], stdout=False, full_filepaths=True)
    with pytest.raises(Exception, match='unsafe path'):
        unzip_http.download_file(f, None, args)
    assert not (tmp_path.parent/'escaped.txt').exists()
