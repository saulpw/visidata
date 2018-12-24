import unittest
from unittest import skip
from unittest.mock import Mock, patch

import visidata
#from visidata import editText, EscapeException


class EditTextTestCase(unittest.TestCase):
    def setUp(self):
        self.scr = Mock()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.chars = []
        visidata.vd.getkeystroke = Mock(side_effect=self.chars)

    def ungetkeystroke(self, *chars):
        self.chars.extend(chars)

    def t(self, keys, result=None, exception=None, **kwargs):
        for k in keys.split():
            self.ungetkeystroke(k)

        if exception:
            with self.assertRaises(exception):
                visidata.editText(self.scr, 0, 0, 0, **kwargs)
        else:
            r = visidata.editText(self.scr, 0, 0, 0, **kwargs)
            self.assertEqual(r, result)

    def tests(self):
        self.t('^J', result='')
        self.t('a b KEY_HOME c d ^A e f ^J', result='efcdab')
        self.t('a b KEY_LEFT 1 KEY_LEFT KEY_LEFT KEY_LEFT 2 ^J', result='2a1b') # Left, past home
        self.t('a b ^C', exception=visidata.EscapeException)
        self.t('a b ^[', exception=visidata.EscapeException)
        self.t('a KEY_DC ^J', result='a')
        self.t('a b KEY_LEFT KEY_DC ^J', result='a')
        self.t('a b KEY_LEFT c KEY_END d ^J', result='acbd')
        self.t('a b KEY_HOME KEY_RIGHT c ^J', result='acb')
        self.t('a b KEY_BACKSPACE c ^J', result='ac')

        # Backspace no longer deletes the first character at the start
        self.t('a b KEY_HOME KEY_BACKSPACE c ^J', result='cab')

        # Backspace works in different combos, including on the mac.
        self.t('a b c KEY_BACKSPACE ^H KEY_LEFT KEY_DC ^J', result='')

        self.t('a b c ^B ^B ^K ^J', result='a')

        self.t('a ^R ^J', result='')
        self.t('a ^R ^J', value='foo', result='foo')

        # With one character is a no-op
        #self.t('a ^T ^J', result='a')

        # Two characters swaps characters
        self.t('a b ^T ^J', result='ba')

        # Home with multiple characters acts like delete
        self.t('a b KEY_HOME ^T ^J', result='b')

        #self.t('^T ^J', result='')
        self.t('a b KEY_LEFT ^U ^J', result='b')
        self.t('a b ^U c ^J', result='c')
