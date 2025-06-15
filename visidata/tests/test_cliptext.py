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
        (iterchars([1,2,3]), 1, '[', 1),
        (iterchars({'a':1, 'b':2, 'c':3}), 1, '{', 1),
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

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('b to', 4, 'b to', 4),
        ('abcde', 8, 'abcde', 5),
        (' jsonl', 5, 'jsonl', 5),
        ('abcdで', 6, 'abcdで', 6),
        ('abcdで', 5, 'bcdで', 5),
        ('でbcdで', 6, 'bcdで', 5),
        ('でbcdefghiで', 10, 'bcdefghiで', 10),
        ('でbcdefghiで', 3, 'iで', 3),
        ('でbcdで', 2, 'で', 2),
        ('でbcdで', 1, '', 0),
        ('でbcdで', 0, '', 0),
        ('でbcdで', -1, '', 0),
    ])
    def test_clipstr_start(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr_start(s, w)
        assert clips == clippeds
        assert clipw == clippedw

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('aAbcで', 6, 'aAbcで', 6),
        ('aAbcで', 7, 'aAbcで', 6),
        ('aAbcで', 1000, 'aAbcで', 6),
        ('aAbcで', 5, '…bcで', 5),
        ('でbcで', 5, '…bcで', 5),
        ('でででででbcで', 5, '…bcで', 5),
        ('でbcで', 3, '…で', 3),
        ('でbcで', 2, '…', 1),
        ('でbcで', 1, '…', 1),
        ('でbcで', 0, '', 0),
        ('でbcで', -1, '', 0),
    ])
    def test_clipstr_start_truncator(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr_start(s, w, truncator='…')
        assert clips == clippeds
        assert clipw == clippedw

    @pytest.mark.parametrize('s, w, clippeds, clippedw', [
        ('1234567890', 6, '12…890', 6),
        ('1234567890', 7, '123…890', 7),
        ('1234567890', 8, '123…7890', 8),
        ('1234567890', 9, '1234…7890', 9),
        ('1234567890', 10, '1234567890', 10),
        ('1234567890', 11, '1234567890', 10),
        ('1234567890', 99, '1234567890', 10),
        # all full-width characters
        ('ででででで', 0,  '', 0),
        ('ででででで', 1,  '…', 1),
        ('ででででで', 2,  '…', 1),
        ('ででででで', 3,  '…で', 3),
        ('ででででで', 4,  '…で', 3),
        ('ででででで', 5,  'で…で', 5),
        ('ででででで', 6,  'で…で', 5),
        ('ででででで', 7,  'で…でで', 7),
        ('ででででで', 8,  'で…でで', 7),
        ('ででででで', 9,  'でで…でで', 9),
        ('ででででで', 10, 'ででででで', 10),
        ('ででででで', 11, 'ででででで', 10),
        ('ででででで', 99, 'ででででで', 10),
        # odd string length, with mix of full-width characters
        ('ででaaでa', 0,  '', 0),
        ('ででaaでa', 1,  '…', 1),
        ('ででaaでa', 2,  '…a', 2),
        ('ででaaででa', 3,  '…a', 2),
        ('ででaaででa', 4,  '…でa', 4),
        ('ででaaででa', 5,  'で…a', 4),
        ('ででaaででa', 6,  'で…でa', 6),
    ])
    def test_clipstr_middle(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr_middle(s, w)
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
