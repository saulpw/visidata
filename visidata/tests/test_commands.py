import pkg_resources
import pytest
from unittest.mock import Mock

import itertools
import visidata

# test separately as needed

inputLines = { 'save-sheet': 'tests/jetsam.csv',  # save to some tmp file
                 'open-file': 'tests/jetsam.csv',  # reopen what was just saved ('o' must come after ^S in the commands list)
                 'save-col': 'tests/flotsam.csv',
                'pyobj-expr': '2+2',            # open the python object for '4'
                 'search-col': 'foo',
                 'searchr-col': 'bar',
                 'select-col-regex': '.',
                 'select-cols-regex': '.',
                 'unselect-col-regex': '.',
                 'unselect-cols-regex': '.',
#                 'e': '',               # no change should not error
                 'go-col-regex': 'Unit',          # column name in sample
                 'go-col-number': '2',
                 'go-row-number': '5',              # go to row 5
                 'addcol-bulk': '1',
                 'addcol-expr': 'Unit',          # just copy the column
                 'split-col': '-',
                 'show-expr': 'OrderDate',
                 'setcol-expr': 'OrderDate',
                 'setcell-expr': 'OrderDate',
                 'setcol-range': 'range(100)',
                 'capture-col': '(.)(.*)',
                 'addcol-subst': r'Unit/(\w)/\1', # the first character
                 'search-cols': 'foo',
                 'searchr-cols': 'bar',
                 'select-cols-regex': '.',
                 'unselect-cols-regex': '.',
                 'random-rows': '3',
              }

@pytest.mark.usefixtures('curses_setup')
class TestCommands:

    def test_baseCommands(self, mock_screen):
        'exec each global command at least once'

        cmdlist = visidata.vd.commands

        vs = visidata.Sheet('test_commands')
        vs.reload()
        vd = visidata.vd
        nerrs = 0
        ntotal = 0
        for longname in cmdlist.keys():
            if 'Sheet' not in cmdlist[longname]:
                continue
            ntotal += 1
            print(longname)
            self.runOneTest(mock_screen, longname)
            vd.sync()
            if vd.lastErrors:
                # longname, execstr, and vd.lastErrors
                print("{0} FAILED: {1}\n\n\n {2}".format(longname, cmdlist[longname]['Sheet'].execstr, '\n'.join('\n'.join(x) for x in vd.lastErrors)))
                nerrs += 1
                break
            vs.checkCursor()
        print('%s/%s commands had errors' % (nerrs, ntotal))

    def runOneTest(self, mock_screen, longname):
            visidata.vd.clearCaches()  # we want vd to return a new VisiData object for each command
            vd = visidata.vd
            vd.scr = mock_screen

            if longname in inputLines:
                line = [ch for ch in inputLines[longname]] + ['^J']
                vd.getkeystroke = Mock(side_effect=line)
            else:
                vd.getkeystroke = Mock(side_effect=['^J'])

            sample_file = pkg_resources.resource_filename('visidata', '../sample_data/sample.tsv')
            vs = visidata.TsvSheet('test_commands', source=visidata.Path(sample_file))
            vs.reload.__wrapped__(vs)
            vs.vd = vd
            vd.sheets = [vs]
            vs.mouseX, vs.mouseY = (4, 4)
            vs.draw(mock_screen)
            vs.execCommand(longname, vdglobals=vars(visidata))
