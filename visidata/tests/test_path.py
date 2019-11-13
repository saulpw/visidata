import unittest
from unittest.mock import Mock

import visidata

class VisiDataPathTestCase(unittest.TestCase):
    def setUp(self):
        self.scr = Mock()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.scr.getmaxyx = lambda: (25, 80)
        import curses
        curses.curs_set = lambda v: None

    def test_withName(self):
        'tests for visidata.Path().with_name'

        file_path = visidata.Path('sample_data/sample.tsv')
        url_path = visidata.Path('https://visidata.org/sample.tsv')

        assert 'sample_data/b.tsv' == str(file_path.with_name('b.tsv')), '{} should be sample_data/b.tsv'.format(file_path.with_name('b.tsv'))
        assert 'sample_data/a/b.tsv' == str(file_path.with_name('a/b.tsv')), '{} should be sample_data/a/b.tsv'.format(file_path.with_name('a/b.tsv'))
        assert "https://visidata.org/b.tsv" == str(url_path.with_name('b.tsv')), '{} should be https://visidata.org/b.tsv'.format(url_path.with_name('b.tsv'))
        assert "https://visidata.org/a/b.tsv" == str(url_path.with_name('b.tsv')), '{} should be https://visidata.org/a/tsv'.format(url_path.with_name('a/b.tsv'))

if __name__ == '__main__':
    unittest.main()
