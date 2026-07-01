from visidata.color import rgb_to_xterm256, xterm256_to_rgb, xterm256_to_css, css_to_xterm256


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
