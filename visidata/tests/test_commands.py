
import unittest
from unittest import skip
from unittest.mock import Mock

import itertools
import visidata

# test separately as needed
expected_errors = [ '^E', 'g', '^R', '^^', 'e', '^J' ]

input_lines = { '^S': 'tests/jetsam.csv',  # save to some tmp file
                 'o': 'tests/jetsam.csv',  # reopen what was just saved ('o' must come after ^S in the commands list)
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

    def test_commands(self):
        'exec each command at least once'
        vs = visidata.SheetObject('test_commands', self)
        vs.reload()
        for keystrokes in itertools.chain(vs.commands.keys(), visidata.base_commands.keys()):
            testname = keystrokes
#            print(testname)
            if testname in expected_errors:
                continue

            if testname in input_lines:
                line = [ch for ch in input_lines[testname]] + ['^J']
                visidata.getkeystroke = Mock(side_effect=line)
            else:
                visidata.getkeystroke = Mock(side_effect=['^J'])

            visidata.vd.cache_clear()  # so vd() returns a new VisiData object for each command
            vd = visidata.vd()
            vs = visidata.SheetObject('test_commands', 'some object')
            vd.scr = self.scr
            vd.push(vs)
            vs.draw(self.scr)
            vs.exec_command(vars(visidata), keystrokes)
