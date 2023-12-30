import pytest
from unittest.mock import Mock, call

import visidata


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
    ])
    def test_clipstr(self, s, w, clippeds, clippedw):
        clips, clipw = visidata.clipstr(s, w)
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
