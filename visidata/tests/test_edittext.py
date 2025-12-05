import pytest
from unittest.mock import Mock, patch

import visidata


class TestEditText:
    @pytest.fixture(autouse=True, scope='function')
    def setUp(self):
        self.chars = []
        visidata.vd.getkeystroke = Mock(side_effect=self.chars)

    @pytest.mark.parametrize('keys, result, kwargs', [
        ('Enter', '', {}),
        ('a b Home c d Ctrl+A e f Enter', 'efcdab', {}),
        ('a b Left 1 Left Left Left 2 Enter', '2a1b', {}), # Left, past home
        ('a b Ctrl+C', None, dict(exception=visidata.EscapeException)),
        ('a b Ctrl+[', None, dict(exception=visidata.EscapeException)),
        ('a Del Enter', 'a', {}),
        ('a b Left Del Enter', 'a', {}),
        ('a b Left c End d Enter', 'acbd', {}),
        ('a b Home Right c Enter', 'acb', {}),
        ('a b Bksp c Enter', 'ac', {}),

        # Backspace no longer deletes the first character at the start
        ('a b Home Bksp c Enter', 'cab', {}),

        # Backspace works in different combos, including on the mac.
        ('a b c Bksp Ctrl+H Left Del Enter', '', {}),

        ('a b c Ctrl+B Ctrl+B Ctrl+K Enter', 'a', {}),

        ('a Ctrl+R Enter', '', {}),
        ('a Ctrl+R Enter', 'foo', dict(value='foo')),

        # Two characters swaps characters
        ('a b Ctrl+T Enter', 'ba', {}),

        # Home with multiple characters acts like delete
        ('a b Home Ctrl+T Enter', 'b', {}),

        ('a b Left Ctrl+U Enter', 'b', {}),
        ('a b Ctrl+U c Enter', 'c', {}),
    ])
    def test_keys(self, mock_screen, keys, result, kwargs):
        self.chars.extend(keys.split())

        exception = kwargs.pop('exception', None)
        widget = visidata.InputWidget(**kwargs)
        if exception:
            with pytest.raises(exception):
                widget.editline(mock_screen, 0, 0, 0, attr=visidata.ColorAttr())
        else:
            r = widget.editline(mock_screen, 0, 0, 0, attr=visidata.ColorAttr())
            assert r == result
