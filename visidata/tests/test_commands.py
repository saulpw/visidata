
import unittest
from unittest import skip
from unittest.mock import Mock

import itertools
import visidata

# test separately as needed
expectedErrors = [ '^R', '^^', 'e', 'ge', '^J', '^S', 'o', 'KEY_BACKSPACE', '^Z', 'p']

inputLines = { '^S': 'tests/jetsam.csv',  # save to some tmp file
                 'o': 'tests/jetsam.csv',  # reopen what was just saved ('o' must come after ^S in the commands list)
                '^X': '2+2',            # open the python object for '4'
                 '/': 'foo',
                 '?': 'bar',
                 '|': '.',
                 '\\': '.',
#                 'e': '',               # no change should not error
                 'c': 'value',          # column name in SheetObject
                 'r': '5',              # go to row 5
                 '=': 'value',          # just copy the column
                 ':': '_',
                 ';': '(.)(.*)',
                 '*': r'value/(\w)/\1', # the first character
                 'g/': 'foo',
                 'g?': 'bar',
                 'g|': '.',
                 'g\\': '.',
                 'P': '50',
              }

@unittest.skip('VisiData singleton not resettable due to addons')
class CommandsTestCase(unittest.TestCase):
    def setUp(self):
        self.scr = Mock()
        self.scr.addstr = Mock()
        self.scr.move = Mock()
        self.scr.getmaxyx = lambda: (25, 80)
        import curses
        curses.curs_set = lambda v: None

    def test_baseCommands(self):
        'exec each global command at least once'

        cmdlist = visidata.baseCommands

        vs = visidata.SheetObject('test_commands', self)
        vs.reload()
        for keystrokes in cmdlist.keys():
            testname = keystrokes
            if testname in expectedErrors:
                continue
#            print(testname)

#            visidata.vd.cache_clear()  # so vd() returns a new VisiData object for each command
            vd = visidata.vd()
            vd.scr = self.scr

            if testname in inputLines:
                line = [ch for ch in inputLines[testname]] + ['^J']
                vd.getkeystroke = Mock(side_effect=line)
            else:
                vd.getkeystroke = Mock(side_effect=['^J'])

            vs = visidata.SheetObject('test_commands', 'some object')
            vs.vd = vd
            vs.reload()
            vd.sheets = [vs]
            vs.draw(self.scr)
            vs.exec_command(cmdlist[keystrokes], vdglobals=vars(visidata))
            self.assertFalse(vd.lastErrors and (keystrokes, cmdlist[keystrokes][2], vd.lastErrors))
            vs.checkCursor()
