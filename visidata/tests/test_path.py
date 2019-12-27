import pytest

import visidata

class TestVisidataPath:

    def test_withName(self):
        'tests for visidata.Path().with_name'

        file_path = visidata.Path('sample_data/sample.tsv')
        url_path = visidata.Path('https://visidata.org/hello/sample.tsv')

        assert 'sample_data/b.tsv' == str(file_path.with_name('b.tsv')), '{} should be sample_data/b.tsv'.format(file_path.with_name('b.tsv'))
        assert 'sample_data/a/b.tsv' == str(file_path.with_name('a/b.tsv')), '{} should be sample_data/a/b.tsv'.format(file_path.with_name('a/b.tsv'))

        assert "https://visidata.org/hello/b.tsv" == str(url_path.with_name('b.tsv')), '{} should be https://visidata.org/hello/b.tsv'.format(url_path.with_name('b.tsv'))
        assert "https://visidata.org/hello/a/b.tsv" == str(url_path.with_name('a/b.tsv')), '{} should be https://visidata.org/hello/a/b.tsv'.format(url_path.with_name('a/b.tsv'))
