import pkg_resources
import pytest
from unittest.mock import Mock

import itertools
import visidata

# test separately as needed

# prefixes which should not be tested
# commands that require curses, and are not
# replayable
nonTested = (
        'syscopy',
        'syspaste',
        'macro',
        'mouse',
        'suspend',
        'breakpoint',
        'redraw',
        'menu',
        'sysopen',
        'open-memusage',
        )

def isTestableCommand(longname, cmdlist):
    if any([longname.startswith(n) for n in nonTested]):
        return False
    return True


inputLines = { 'save-sheet': 'jetsam.csv',  # save to some tmp file
                'save-all': 'lagan.csv',
                 'open-file': 'jetsam.csv',  # reopen what was just saved ('o' must come after ^S in the commands list)
                 'save-col': 'flotsam.csv',
                 'save-col-keys': 'debris.csv',
                'pyobj-expr': '2+2',            # open the python object for '4'
                'edit-cell': '3',
                 'search-col': 'foo',
                 'searchr-col': 'bar',
                 'select-col-regex': '.',
                 'select-cols-regex': '.',
                 'unselect-col-regex': '.',
                 'unselect-cols-regex': '.',
                 'edit-cell': '',               # no change should not error
                 'go-col-regex': 'Unit',          # column name in sample
                 'go-col-number': '2',
                 'go-row-number': '5',              # go to row 5
                 'addcol-bulk': '1',
                 'addcol-expr': 'Unit',          # just copy the column
                 'addcol-incr-step': '2',
                 'setcol-incr-step': '2',
                 'setcol-format-enum': '1=cat',
                 'split-col': '-',
                 'show-expr': 'OrderDate',
                 'setcol-expr': 'OrderDate',
                 'setcell-expr': 'OrderDate',
                 'setcol-range': 'range(100)',
                 'repeat-input-n': '1',
                 'capture-col': '(.)(.*)',
                 'addcol-subst': r'Units/(\w)/\1', # the first character
                 'search-cols': 'foo',
                 'searchr-cols': 'bar',
                 'select-cols-regex': '.',
                 'select-expr': 'OrderDate',
                 'unselect-expr': 'OrderDate',
                 'unselect-cols-regex': '.',
                 'random-rows': '3',
                 'import-python': 'math',
                 'pyobj-expr-row': 'Units + "s"',            # open the python object for '4'
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
            if not isTestableCommand(longname, cmdlist):
                continue
            ntotal += 1
            print(longname)
            self.runOneTest(mock_screen, longname)
            vd.sync()
            if vd.lastErrors:
                # longname, execstr, and vd.lastErrors
                print("FAILED: {0}".format(longname), '\n'.join('\n'.join(x) for x in vd.lastErrors))
                nerrs += 1
                break
            vs.checkCursor()
        print('%s/%s commands had errors' % (nerrs, ntotal))
        if nerrs > 0:
            assert False

    def runOneTest(self, mock_screen, longname):
        visidata.vd.clearCaches()  # we want vd to return a new VisiData object for each command
        vd = visidata.vd
        vd.cmdlog.rows = []
        vd.scr = mock_screen

        if longname in inputLines:
            line = [ch for ch in inputLines[longname]] + ['^J']
            vd.getkeystroke = Mock(side_effect=line)
        else:
            vd.getkeystroke = Mock(side_effect=['^J'])

        sample_file = pkg_resources.resource_filename('visidata', 'tests/sample.tsv')
        vs = visidata.TsvSheet('test_commands', source=visidata.Path(sample_file))
        vs.reload.__wrapped__(vs)
        vs.vd = vd
        vd.sheets = [vs]
        vd.allSheets = [vs]
        vs.mouseX, vs.mouseY = (4, 4)
        vs.draw(mock_screen)
        vs.execCommand(longname, vdglobals=vars(visidata))
