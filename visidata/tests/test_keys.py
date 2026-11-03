import curses
from unittest.mock import Mock

import pytest

import visidata
from visidata import vd
from visidata._input import InputWidget


# v3.4 prettykeys overhaul (#2594): curses key codes render as human-readable
# names. Pure translation, asserted directly.
class TestPrettyKeys:
    def test_prettykeys(self):
        assert vd.prettykeys('^S') == 'Ctrl+S'
        assert vd.prettykeys('^M') == 'Enter'
        assert vd.prettykeys(' ') == 'Space'
        assert vd.prettykeys('kUP') == 'Shift+Up'      # curses shifted-arrow code
        assert vd.prettykeys('KEY_HOME') == 'Home'
        assert vd.prettykeys('g^S') == 'gCtrl+S'        # g prefix preserved, ^ translated


class TestInputWidget:
    @pytest.mark.parametrize('key, expected', [('Alt+Space', ' '), ('Alt+A', 'A')])
    def test_alt_sequences_are_treated_as_literal_text(self, key, expected):
        widget = InputWidget()
        widget.handle_key(key, None)
        assert widget.value == expected

    @pytest.mark.parametrize('character, keyname', [('L', b'L'), (' ', b' ')])
    def test_integer_printable_keys(self, monkeypatch, mock_screen, character, keyname):
        monkeypatch.setattr(vd, 'pendingKeys', [])
        monkeypatch.setattr(vd, 'get_wch', Mock(return_value=ord(character)))
        monkeypatch.setattr(vd, 'drainPendingKeys', Mock(return_value=False))
        monkeypatch.setattr(curses, 'reset_prog_mode', Mock())
        monkeypatch.setattr(curses, 'keyname', Mock(return_value=keyname))
        monkeypatch.setattr(vd, 'drawRightStatus', Mock())

        key = visidata.VisiData.getkeystroke(vd, mock_screen)
        widget = InputWidget()
        widget.handle_key(key, mock_screen)

        expected_key = 'Shift+L' if character == 'L' else 'Space'
        assert key == expected_key
        assert widget.value == character
