import unittest
from unittest import skip
from unittest.mock import Mock, patch

from visidata.tui import edit_text, Key, Shift, Ctrl, EscapeException


class EditTextTestCase(unittest.TestCase):
    def setUp(self):
        self.scr = Mock()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.chars=[]
        self.scr.getch = Mock(side_effect=self.chars)

    def mock_getch(self, *chars):
        self.chars.extend(chars)

    def t(self, *keys, result=None, exception=None, **kwargs):
        for k in keys:
            if isinstance(k, str):
                for ch in k:
                    self.mock_getch(ord(ch))
            else:
                self.mock_getch(k)
        if exception:
            with self.assertRaises(exception):
                edit_text(self.scr, 0, 0, 0, **kwargs)
        else:
            r = edit_text(self.scr, 0, 0, 0, **kwargs)
            self.assertEqual(r, result)

    def tests(self):
        self.t(Key.ENTER, result='')
        self.t(Key.IC, 'ab', Key.HOME, 'cd', Ctrl.A, 'ef', Key.ENTER, result='efcdab')
        self.t(Key.IC, 'ab', Key.LEFT, '1', Key.LEFT, Key.LEFT, Key.LEFT, '2', Key.ENTER, result='2a1b') # Left, past home
        self.t(Key.IC, 'ab', Ctrl.C, exception=EscapeException)
        self.t(Key.IC, 'ab', Key.ESC, exception=EscapeException)
        self.t(Key.IC, 'a', Key.DC, Key.ENTER, result='a')
        self.t(Key.IC, 'ab', Key.LEFT, Key.DC, Key.ENTER, result='a')
        self.t(Key.IC, 'ab', Key.LEFT, 'c', Key.END, 'd', Key.ENTER, result='acbd')
        self.t(Key.IC, 'ab', Key.HOME, Key.RIGHT, 'c', Key.ENTER, result='acb')
        self.t(Key.IC, 'ab', Key.BACKSPACE, 'c', Key.ENTER, result='ac')

        # Backspace deletes the first character at the start
        self.t(Key.IC, 'ab', Key.HOME, Key.BACKSPACE, 'c', Key.ENTER, result='cb')

        # Backspace works in different combos, including on the mac.
        self.t('abc', Key.BACKSPACE, Ctrl.H, Key.DEL, Key.ENTER, result='')

        # ^J works the same way as ENTER.
        self.t('abc', Ctrl.J, result='abc')

        self.t('abc', Ctrl.B, Ctrl.B, Ctrl.K, Key.ENTER, result='a')

        self.t('a', Ctrl.R, Key.ENTER, result='')
        self.t('a', Ctrl.R, Key.ENTER, value='foo', result='foo')

        # With one character is a no-op
        #self.t('a', Ctrl.T, Key.ENTER, result='a')

        # Two characters swaps characters
        self.t('ab', Ctrl.T, Key.ENTER, result='ba')

        # Home with multiple characters acts like delete
        self.t('ab', Key.HOME, Ctrl.T, Key.ENTER, result='b')

        #self.t(Ctrl.T, Key.ENTER, result='')
        self.t('ab', Key.LEFT, Ctrl.U, Key.ENTER, result='b')
        self.t('ab', Ctrl.U, 'c', Key.ENTER, result='c')
