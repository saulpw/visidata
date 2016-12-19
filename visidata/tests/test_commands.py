
import unittest
from unittest import skip
from unittest.mock import Mock

import curses
import visidata
import visidata.tui
from visidata.tui import Key

# test separately as needed
expected_errors = [ '^E', 'g', '^R', '^^', 'gd', 'e', '^J' ]

input_lines = { '^S': '/tmp/blah.csv',  # save to some tmp file
                 'o': '/tmp/blah.csv',  # reopen what was just saved ('o' must come after ^S in the commands list)
                '^O': '2+2',            # open the python object for '4'
                 '/': 'foo',
                 '?': 'bar',
                 '|': '.',
                 '\\': '.',
#                 'e': '',               # no change should not error
                 'c': 'value',          # column name in SheetObject
                 'r': '5',              # go to row 5
                 '=': 'value',          # just copy the column
                 ':': r'value/(\w)/\1', # the first character
                 'g/': 'foo',
                 'g?': 'bar',
                 'g|': '.',
                 'g\\': '.',
                 'R': '.',
              }

class CommandsTestCase(unittest.TestCase):
    def setUp(self):
        self.scr = Mock()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.scr.getmaxyx = lambda: (25, 80)
        curses.initscr()  # activate keyname()
        curses.endwin()   # but stay in terminal mode

    def test_commands(self):
        'exec each command at least once'
        vs = visidata.SheetObject('test_commands', self)
        for prefixes, cmd in vs.commands:
            testname = prefixes + visidata.tui.keyname(cmd)
#            print(testname)
            if testname in expected_errors:
                continue

            if testname in input_lines:
                line = [Key(ch) for ch in input_lines[testname]] + [Key.ENTER]
                self.scr.getch = Mock(side_effect=line)
            else:
                self.scr.getch = Mock(side_effect=[visidata.tui.Key.ENTER])

            visidata.vd.cache_clear()  # so vd() returns a new VisiData object for each command
            vd = visidata.vd()
            vs = visidata.SheetObject('test_commands', 'some object')
            vd.scr = self.scr
            vd.push(vs)
            vs.draw(self.scr)
            visidata.set_sheet(vs)
            vs.exec_command(vars(visidata), prefixes, cmd)
