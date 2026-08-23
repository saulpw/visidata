import curses

import pytest

from visidata.color import ColorMaker, rgb_to_xterm256, xterm256_to_rgb, xterm256_to_css, css_to_xterm256


@pytest.fixture
def fake_curses(monkeypatch):
    'Mimic initialized curses for a terminal with the given COLORS/COLOR_PAIRS.'
    def _setup(ncolors, npairs):
        def init_pair(pairnum, fg, bg):
            # py3.10+ raises ValueError (not curses.error) for out-of-range args  #1227
            if pairnum > npairs - 1:
                raise ValueError(f'Color pair is greater than COLOR_PAIRS-1 ({npairs-1}).')
            if fg > ncolors - 1 or bg > ncolors - 1:
                raise ValueError(f'Color number is greater than COLORS-1 ({ncolors-1}).')

        monkeypatch.setattr(curses, 'COLORS', ncolors, raising=False)
        monkeypatch.setattr(curses, 'COLOR_PAIRS', npairs, raising=False)
        monkeypatch.setattr(curses, 'init_pair', init_pair)
        monkeypatch.setattr(curses, 'color_pair', lambda pairnum: pairnum << 8)
        monkeypatch.setattr(curses, 'has_colors', lambda: ncolors > 0)
        return ColorMaker()
    return _setup


class TestColorMaker:
    def test_8color_terminal(self, fake_curses):
        'TERM=xterm/ansi: 8 colors and 64 pairs; basic colors must still resolve.  #3206'
        cm = fake_curses(8, 64)
        assert cm._get_colornum('red') == curses.COLOR_RED
        assert cm._get_colornum('green') == curses.COLOR_GREEN
        assert cm._get_colornum('1') == 1
        assert cm._get_colornum('114') is None   # beyond 8 colors
        assert cm._get_colornum('236') is None
        assert cm._colornames_to_cattr('114 green').fg == curses.COLOR_GREEN  # fallback color

    def test_colorless_terminal(self, fake_curses):
        'TERM=vt100: no colors, no pairs; must not raise.  #3206'
        cm = fake_curses(0, 0)
        assert cm._get_colornum('red') is None
        assert cm._get_colorpair(-1, -1, 'default') == 0

    def test_pairnum_within_terminal_limit(self, fake_curses):
        'allocated pairnums must stay within COLOR_PAIRS, recycling as needed.  #3206'
        cm = fake_curses(8, 64)
        for fg in range(8):
            for bg in range(8):
                cm._get_colorpair(fg, bg, f'{fg} on {bg}')  # 64 distinct pairs > 63 usable
        assert all(pairnum < 64 for pairnum, _ in cm.color_pairs.values())


# v3.4 xterm256 <-> rgb/css conversion helpers (visidata/color.py). Pure functions,
# so asserted directly rather than through the UI.
class TestXterm256:
    def test_conversions(self):
        assert rgb_to_xterm256(255, 0, 0) == 196       # pure red
        assert rgb_to_xterm256(0, 0, 0) == 16          # black (color-cube origin, not 0)
        assert rgb_to_xterm256(255, 255, 255) == 231   # white (color-cube max, not 15)
        assert xterm256_to_rgb(196) == (255, 0, 0)
        assert xterm256_to_css(196) == '#ff0000'
        assert css_to_xterm256('#ff0000') == 196
        assert css_to_xterm256('#000000') == 16
        # round-trips through the color cube for a saturated primary
        assert xterm256_to_rgb(rgb_to_xterm256(255, 0, 0)) == (255, 0, 0)
        assert css_to_xterm256(xterm256_to_css(196)) == 196
