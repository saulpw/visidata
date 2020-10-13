import pytest
from unittest.mock import Mock, patch

import visidata


class TestEditText:
    @pytest.fixture(autouse=True, scope='function')
    def setUp(self):
        self.chars = []
        visidata.vd.getkeystroke = Mock(side_effect=self.chars)

    @pytest.mark.parametrize('keys, result, kwargs', [
        ('^J', '', {}),
        ('a b KEY_HOME c d ^A e f ^J', 'efcdab', {}),
        ('a b KEY_LEFT 1 KEY_LEFT KEY_LEFT KEY_LEFT 2 ^J', '2a1b', {}), # Left, past home
        ('a b ^C', None, dict(exception=visidata.EscapeException)),
        ('a b ^[', None, dict(exception=visidata.EscapeException)),
        ('a KEY_DC ^J', 'a', {}),
        ('a b KEY_LEFT KEY_DC ^J', 'a', {}),
        ('a b KEY_LEFT c KEY_END d ^J', 'acbd', {}),
        ('a b KEY_HOME KEY_RIGHT c ^J', 'acb', {}),
        ('a b KEY_BACKSPACE c ^J', 'ac', {}),

        # Backspace no longer deletes the first character at the start
        ('a b KEY_HOME KEY_BACKSPACE c ^J', 'cab', {}),

        # Backspace works in different combos, including on the mac.
        ('a b c KEY_BACKSPACE ^H KEY_LEFT KEY_DC ^J', '', {}),

        ('a b c ^B ^B ^K ^J', 'a', {}),

        ('a ^R ^J', '', {}),
        ('a ^R ^J', 'foo', dict(value='foo')),

        # Two characters swaps characters
        ('a b ^T ^J', 'ba', {}),

        # Home with multiple characters acts like delete
        ('a b KEY_HOME ^T ^J', 'b', {}),

        ('a b KEY_LEFT ^U ^J', 'b', {}),
        ('a b ^U c ^J', 'c', {}),
    ])
    def test_keys(self, mock_screen, keys, result, kwargs):
        self.chars.extend(keys.split())

        exception = kwargs.pop('exception', None)
        if exception:
            with pytest.raises(exception):
                visidata.vd.editline(mock_screen, 0, 0, 0, **kwargs)
        else:
            r = visidata.vd.editline(mock_screen, 0, 0, 0, **kwargs)
            assert r == result
