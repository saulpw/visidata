# Copyright (C) 2016 Paul Watts
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import curses
import unittest
from curses.ascii import DEL
from unittest import skip
from unittest.mock import Mock, patch

from visidata.edittext import editText
from visidata.exceptions import VEscape
from visidata.keys import ENTER, ESC, ctrl

from .mocks import VisiData, WindowObject


class EditTextTestCase(unittest.TestCase):
    def setUp(self):
        self.vd = VisiData()
        self.vd.status = Mock()

        self.scr = WindowObject()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.scr.getch = Mock(side_effect=[ENTER])

    def mock_getch(self, *chars):
        self.scr.getch = Mock(side_effect=chars)

    def test_simple(self):
        """
        Simple test to check mocks.
        """
        self.scr.getch = Mock(side_effect=[ENTER])
        result = editText(self.vd, self.scr, 0, 0, 0)

        self.vd.status.assert_called_with('""')
        self.assertEqual(result, "")

    def test_home(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_HOME,
                        ord('c'), ord('d'), ctrl('a'),
                        ord('e'), ord('f'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)

        self.assertEqual(result, "efcdab")

    def test_left(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_LEFT, ord('1'),
                        # Left past home
                        curses.KEY_LEFT, curses.KEY_LEFT, curses.KEY_LEFT,
                        ord('2'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)

        self.assertEqual(result, "2a1b")

    def test_escape(self):
        self.mock_getch(ord('a'), ord('b'), ctrl('c'))
        with self.assertRaisesRegex(VEscape, '\^C'), patch('curses.keyname', return_value=b'^C'):
            editText(self.vd, self.scr, 0, 0, 0)

        self.mock_getch(ord('a'), ord('b'), ESC)
        with self.assertRaisesRegex(VEscape, 'xxx'), patch('curses.keyname', return_value=b'xxx'):
            editText(self.vd, self.scr, 0, 0, 0)

    def test_delchar(self):
        self.mock_getch(ord('a'), curses.KEY_DC, ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'a')

        self.mock_getch(ord('a'), ord('b'), curses.KEY_LEFT, curses.KEY_DC, ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'a')

    def test_end(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_LEFT, ord('c'), curses.KEY_END, ord('d'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'acbd')

    def test_right(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_HOME, curses.KEY_RIGHT, ord('c'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'acb')

    def test_backspace(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_BACKSPACE, ord('c'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'ac')

    def test_backspace_first(self):
        """
        Backspace deletes the first character at the start
        """
        self.mock_getch(ord('a'), ord('b'), curses.KEY_HOME, curses.KEY_BACKSPACE, ord('c'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'cb')

    def test_backspace_types(self):
        """
        Backspace works in different combos, including on the mac.
        """
        self.mock_getch(ord('a'), ord('b'), ord('c'), curses.KEY_BACKSPACE, ctrl('h'), DEL, ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, '')

    def test_enter(self):
        """
        ^J works the same way as ENTER.
        """
        self.mock_getch(ord('a'), ord('b'), ord('c'), ctrl('j'))
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'abc')

    def test_truncate(self):
        self.mock_getch(ord('a'), ord('b'), ord('c'), ctrl('b'), ctrl('b'), ctrl('k'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'a')

    def test_reset(self):
        self.mock_getch(ord('a'), ctrl('r'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, '')

        self.mock_getch(ord('a'), ctrl('r'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0, value='foo')
        self.assertEqual(result, 'foo')

    def test_swap(self):
        """
        With one character is a no-op
        """
        self.mock_getch(ord('a'), ctrl('t'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'a')

    def test_swap_two(self):
        """
        Two characters swaps characters
        """
        self.mock_getch(ord('a'), ord('b'), ctrl('t'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'ba')

    def test_swap_home(self):
        """
        Home with multiple characters acts like delete
        """
        self.mock_getch(ord('a'), ord('b'), curses.KEY_HOME, ctrl('t'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'b')

    @skip("Broken, this throws an exception")
    def test_swap_empty(self):
        """
        This is a no-op
        """
        self.mock_getch(ctrl('t'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, '')

    def test_del_front(self):
        self.mock_getch(ord('a'), ord('b'), curses.KEY_LEFT, ctrl('u'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'b')

        self.mock_getch(ord('a'), ord('b'), ctrl('u'), ord('c'), ENTER)
        result = editText(self.vd, self.scr, 0, 0, 0)
        self.assertEqual(result, 'c')

    # TODO: Test ctrl-V. What does it do?
    # TODO: Test prompt
    # TODO: Test value
    # TODO: Test fillchar
    # TODO: Test colors
