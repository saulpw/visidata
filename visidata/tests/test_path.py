import io
import pytest

from visidata import Path
from visidata.path import RepeatFile, BytesIOWrapper

class TestVisidataPath:

    def test_withName(self):
        'tests for visidata.Path().with_name'

        file_path = Path('sample_data/sample.tsv')
        url_path = Path('https://visidata.org/hello/sample.tsv')

        assert 'sample_data/b.tsv' == str(file_path.with_name('b.tsv')), '{} should be sample_data/b.tsv'.format(file_path.with_name('b.tsv'))
        assert 'sample_data/a/b.tsv' == str(file_path.with_name('a/b.tsv')), '{} should be sample_data/a/b.tsv'.format(file_path.with_name('a/b.tsv'))

        assert "https://visidata.org/hello/b.tsv" == str(url_path.with_name('b.tsv')), '{} should be https://visidata.org/hello/b.tsv'.format(url_path.with_name('b.tsv'))
        assert "https://visidata.org/hello/a/b.tsv" == str(url_path.with_name('a/b.tsv')), '{} should be https://visidata.org/hello/a/b.tsv'.format(url_path.with_name('a/b.tsv'))

        assert Path('foo.a.b').base_stem == 'foo.a'
        assert Path('foo.a.b').ext == 'b'
        assert Path('foo').ext == ''
        assert Path('foo').base_stem == 'foo'
        assert Path('foo.').ext == ''
        # assert Path('foo.').base_stem == 'foo.' # only 'foo' since python 3.14
        assert Path('foo..').ext == ''
        assert Path('foo..').base_stem == 'foo..'
        assert Path('.foo').ext == ''
        assert Path('.foo').base_stem == '.foo'


    def test_opentwice(self):
        'fresh iterator for each open'
        p = Path('test', fptext=io.StringIO('<html>'))
        a = next(p.open())
        b = next(p.open())
        assert a == b

    def test_iterdir_yields_visidata_paths(self):  # #2188
        for p in Path('/tmp').iterdir():
            assert isinstance(p, Path), f'{p} is {type(p)}, expected visidata.Path'
            break  # just check the first one

    def test_name_returns_full_filename(self):  # #2188
        assert Path('foo.csv').name == 'foo.csv'
        assert Path('/tmp/bar.tsv').name == 'bar.tsv'
        assert Path('foo').name == 'foo'
        assert Path('foo.csv.gz').name == 'foo.csv.gz'
        assert Path('foo.csv.gz').ext == 'csv'
        assert Path('foo.csv.gz').compression == 'gz'
        assert Path('foo.vds.zst').ext == 'vds'
        assert Path('foo.vds.zst').compression == 'zst'
        assert Path('foo.vds.zstd').ext == 'vds'  #2286
        assert Path('foo.vds.zstd').compression == 'zstd'  #2286

    def test_repeatfile_bytesiowrapper(self):  # #2829
        rf = RepeatFile(iter(['hello\n', 'world\n']))
        bio = BytesIOWrapper(rf)
        data = bio.read()
        assert isinstance(data, bytes)
        assert b'hello' in data
