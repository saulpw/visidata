import curses

import pytest

from visidata import vd, VisiData


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


class GetchScreen:
    def __init__(self, keys):
        self.keys = iter(keys)

    def getch(self):
        return next(self.keys, -1)

    def timeout(self, value):
        pass


class GetWchScreen(GetchScreen):
    def get_wch(self):
        k = self.getch()
        if k == -1:
            raise curses.error('no char ready')
        return chr(k) if k < 256 else k


@pytest.mark.parametrize('screen_class', [GetchScreen, GetWchScreen])
@pytest.mark.parametrize('keys, expected', [
    ([ord('L')], 'L'),
    ([ord(' ')], ' '),
    ([ord('x')], 'x'),
    ([ord('0')], '0'),
    ([ord('!')], '!'),
    ([ord('~')], '~'),
    ([9], 'Tab'),
    ([127], 'Ctrl+?'),
    ([curses.KEY_UP], 'Up'),
    ([27], 'Esc'),
    ([27, ord('x')], 'Alt+x'),
    ([27, ord('L')], 'Alt+Shift+L'),
    ([27, ord(' ')], 'Alt+Space'),
    ([27, curses.KEY_UP], 'Alt+Up'),
])
def test_getkeystroke(screen_class, keys, expected, monkeypatch):
    keynames = {k: bytes([k]) for k in range(32, 127)}
    keynames.update({9: b'^I', 27: b'^[', 127: b'^?', curses.KEY_UP: b'KEY_UP'})
    monkeypatch.setattr(curses, 'keyname', keynames.__getitem__)
    instance = VisiData()
    instance.prettykeys_trdict = vd.prettykeys_trdict
    monkeypatch.setattr(instance, 'get_curses_timeout', lambda: 0)

    assert instance.getkeystroke(screen_class(keys)) == expected
    assert instance.pendingKeys == []
