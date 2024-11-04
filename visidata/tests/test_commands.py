import pytest
from unittest.mock import Mock

import itertools
import visidata
from pathlib import Path

# test separately as needed

# prefixes which should not be tested
# commands that require curses, and are not
# replayable
nonTested = (
        'toggle-profile',
        'syscopy',
        'syspaste',
        'open-syspaste',
        'macro',
        'mouse',
        'add-subreddits',
        'add-submissions',
        'open-zulip',
        'suspend',
        'open-memstats',  # TODO add testing support
        'plot-column-ext',
        'plot-numerics-ext',
        'reload-every',
        'reload-modified',
        'reload-rows',
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
                 'search-keys': 'foo',
                 'search-col': 'foo',
                 'searchr-col': 'bar',
                 'select-col-regex': '.',
                 'select-cols-regex': '.',
                 'unselect-col-regex': '.',
                 'exec-python': 'import time',
                 'unselect-cols-regex': '.',
                 'go-col-regex': 'Units',          # column name in sample
                 'go-col-name': 'Units',           # column name in sample
                 'go-col-number': '2',
                 'go-row-number': '5',              # go to row 5
                 'addcol-bulk': '1',
                 'addcol-expr': 'Units',          # just copy the column
                 'assert-expr': 'sheet.column(\"Units\")',
                 'show-command-info': 'select-row',
                 'assert-expr-row': 'Units',
                 'addcol-incr-step': '2',
                 'setcol-incr-step': '2',
                 'setcol-iter': 'range(1, 100)',
                 'setcol-format-enum': '1=cat',
                 'open-ping': 'github.com',
                 'setcol-input': '5',
                 'show-expr': 'OrderDate',
                 'setcol-expr': 'OrderDate',
                 'open-ping': 'localhost',
                 'setcell-expr': 'OrderDate',
                 'setcol-range': 'range(100)',
                 'repeat-input-n': '1',
                 'addcol-regex-subst': dict(before=r'Units/(\w)', after=r'\1'), # the first character
                 'search-cols': 'foo',
                 'searchr-cols': 'bar',
                 'select-cols-regex': '.',
                 'select-expr': 'OrderDate',
                 'setcol-fake': 'name',
                 'unselect-expr': 'OrderDate',
                 'unselect-cols-regex': '.',
                 'random-rows': '3',
                 'select-random': '3',
                 'import-python': 'math',
                 'pyobj-expr-row': 'Units + "s"',            # open the python object for '4'
                 'expand-col-depth': '0',
                 'contract-col-depth': '0',
                 'contract-cols-depth': '0',
                 'expand-cols-depth': '0',
                 'save-cmdlog': 'test_commands.vdj',
                 'aggregate-col': 'mean',
                 'memo-aggregate': 'count',
                 'memo-cell': 'memoname',
                 'addcol-shell': '',
                 'theme-input': 'light',
                 'add-rows': '1',
                 'join-sheets-top2': 'append',
                 'join-sheets-all': 'append',
                 'resize-col-input': '10',
                 'resize-cols-input': '10',
                 'resize-height-input': '10',
                 'melt-regex': '(.*)_(.*)',
                 'addcol-split': '-',
                 'addcol-capture': '(.*)_(.*)',
                 'slide-left-n': '2',
                 'slide-right-n': '1',
                 'slide-down-n': '1',
                 'slide-up-n': '1',
                 'addcol-window': '0 2',
                 'select-around-n': '1',
                 'sheet': '',
                 'col': 'Units',
                 'row': '5',
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
            cmd = vs.getCommand(longname)
            if cmd and cmd.deprecated:
                continue
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

        # cleanup
        for f in ['flotsam.csv', 'debris.csv', 'jetsam.csv', 'lagan.csv', 'test_commands.vdj']:
            pf = Path(f)
            if pf.exists: pf.unlink()


    def runOneTest(self, mock_screen, longname):
        visidata.vd.clearCaches()  # we want vd to return a new VisiData object for each command
        vd = visidata.vd
        vd.cmdlog.rows = []
        vd.scr = mock_screen

        if longname in inputLines:
            line = [ch for ch in inputLines[longname]] + ['Enter']
            vd.getkeystroke = Mock(side_effect=line)
        else:
            vd.getkeystroke = Mock(side_effect=['Enter'])

        sample_file = vd.pkg_resources_files(visidata) / 'tests/sample.tsv'
        vs = visidata.TsvSheet('test_commands', source=visidata.Path(sample_file))
        cmd = vs.getCommand(longname)
        if not cmd:
            vd.warning(f'command cannot be tested on TsvSheet, skipping:  {longname}')
            return
        vs.reload.__wrapped__(vs)
        vs.vd = vd
        vd.sheets = [vs]
        vd.allSheets = [vs]
        vs.mouseX, vs.mouseY = (4, 4)
        vs.draw(mock_screen)
        vs._scr = mock_screen
        if longname in inputLines:
            vd.currentReplayRow = vd.cmdlog.newRow(longname=longname, input=inputLines[longname])
        else:
            vd.currentReplayRow = vd.cmdlog.newRow(longname=longname)
        vs.execCommand(longname, vdglobals=vd.getGlobals())
