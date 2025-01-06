import pytest
from unittest.mock import Mock, call

import visidata
from visidata import iterchars


class TestClipText:
    @pytest.mark.parametrize('s, dispw', [
        ('abcdef', 6),
        ('桜 高橋', 7),
        ('[:onclick sidebar-toggle][:reverse] b to toggle sidebar [:]', 21),
    ])
    def test_dispwidth(self, s, dispw):
        assert visidata.dispwidth(s) == dispw

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('b to', 4, 'b to', 4),
        ('abcde', 8, 'abcde', 5),
        (' jsonl', 5, ' jso…', 5),
        ('abcdで', 6, 'abcdで', 6),
        ('abcdで', 5, 'abcd…', 5),
        ('a', 1, 'a', 1),
        ('ab', 1, '…', 1),
        ('abc', 2, 'a…', 2),
        ('で', 1, '…', 1),
        ('でで', 1, '…', 1),
        ('でで', 2, '…', 1),
        ('でで', 3, 'で…', 3),
        ('ででで', 4, 'で…', 3),
        ('ででで', 5, 'でで…', 5),
        ('', 1, '', 0),
        ('', None, '', 0),
        ('abcdef', None, 'abcdef', 6),
        ('ででで', None, 'ででで', 6),
        ('で'*100, None, 'で'*100, 2*100),
        (iterchars([1,2,3]), 4, '[3]…', 4),
        (iterchars([1,2,3]), 7, '[3] 1;…', 7),
        (iterchars([1,2,3]), 9, '[3] 1; 2…', 9),
        (iterchars([1,2,3]), 11, '[3] 1; 2; 3', 11),
        (iterchars([1,2,3]), 12, '[3] 1; 2; 3', 11),
        (iterchars({'a':1, 'b':2, 'c':3}), 7, '{3} a=…', 7),
        (iterchars({'a':1, 'b':2, 'c':3}), 15, '{3} a=1 b=2 c=3', 15),
        (iterchars({'a':1, 'b':2, 'で':3}), 13, '{3} a=1 b=2 …', 13),
        (iterchars({'a':1, 'b':2, 'で':3}), 16, '{3} a=1 b=2 で=3', 16),
    ])
    def test_clipstr(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr(s, w)
        assert clips == clippeds
        assert clipw == clippedw

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('b to', 4, 'b to', 4),
        ('abcde', 8, 'abcde', 5),
        (' jsonl', 5, ' jsあ', 5),
        ('abcdで', 6, 'abcdで', 6),
        ('abcdで', 5, 'abcあ', 5),
        ('a', 1, 'a', 1),
        ('ab', 1, 'a', 1),
        ('abc', 2, 'あ', 2),
        ('で', 1, '', 0),
        ('でで', 1, '', 0),
        ('でで', 2, 'あ', 2),
        ('でで', 3, 'あ', 2),
        ('ででで', 4, 'であ', 4),
        ('ででで', 5, 'であ', 4),
        ('', 1, '', 0),
        ('', None, '', 0),
        ('abcdef', None, 'abcdef', 6),
        ('ででで', None, 'ででで', 6),
        ('で'*100, None, 'で'*100, 2*100),
    ])
    def test_clipstr_wide_truncator(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr(s, w, truncator='あ')
        assert clips == clippeds
        assert clipw == clippedw

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('b to', 4, 'b to', 4),
        ('abcde', 8, 'abcde', 5),
        (' jsonl', 5, ' json', 5),
        ('abcdで', 6, 'abcdで', 6),
        ('abcdで', 5, 'abcd', 4),
        ('a', 1, 'a', 1),
        ('ab', 1, 'a', 1),
        ('abc', 2, 'ab', 2),
        ('で', 1, '', 0),
        ('でで', 1, '', 0),
        ('でで', 2, 'で', 2),
        ('でで', 3, 'で', 2),
        ('ででで', 4, 'でで', 4),
        ('ででで', 5, 'でで', 4),
        ('', 1, '', 0),
        ('', None, '', 0),
        ('abcdef', None, 'abcdef', 6),
        ('ででで', None, 'ででで', 6),
        ('で'*100, None, 'で'*100, 2*100),
    ])
    def test_clipstr_empty_truncator(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr(s, w, truncator='')
        assert clips == clippeds
        assert clipw == clippedw

    def test_clipdraw_chunks(self):
        prechunks = [
            ('', 'x'),
            ('', 'jsonl'),
        ]
        scr = Mock()
        scr.getmaxyx.return_value = (80,25)
        visidata.clipdraw_chunks(scr, 0, 0, prechunks, visidata.ColorAttr(), w=5)
        scr.addstr.assert_has_calls([
                call(0, 0, 'x', 0),
                call(0, 1, 'jso…', 0),
        ], any_order=True)
