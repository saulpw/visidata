from visidata import vd


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
