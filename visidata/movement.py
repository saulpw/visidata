import itertools
import re

from visidata import vd, VisiData, error, status, BaseSheet, Sheet, Column, fail, Progress, globalCommand, ALT

__all__ = ['rotateRange']

def rotateRange(n, idx, reverse=False):
    'Wraps an iter starting from idx. Yields indices from idx to n and then 0 to idx.'
    if reverse:
        rng = range(idx-1, -1, -1)
        rng2 = range(n-1, idx-1, -1)
    else:
        rng = range(idx+1, n)
        rng2 = range(0, idx+1)

    wrapped = False
    with Progress(total=n) as prog:
        for r in itertools.chain(rng, rng2):
            prog.addProgress(1)
            if not wrapped and r in rng2:
                status('search wrapped')
                wrapped = True
            yield r

@Sheet.api
def pageLeft(self):
    '''Redraw page one screen to the left.

    Note: keep the column cursor in the same general relative position:

     - if it is on the furthest right column, then it should stay on the
       furthest right column if possible

     - likewise on the left or in the middle

    So really both the `leftIndex` and the `cursorIndex` should move in
    tandem until things are correct.'''

    targetIdx = self.leftVisibleColIndex  # for rightmost column
    firstNonKeyVisibleColIndex = self.visibleCols.index(self.nonKeyVisibleCols[0])
    while self.rightVisibleColIndex != targetIdx and self.leftVisibleColIndex > firstNonKeyVisibleColIndex:
        self.cursorVisibleColIndex -= 1
        self.leftVisibleColIndex -= 1
        self.calcColLayout()  # recompute rightVisibleColIndex

    # in case that rightmost column is last column, try to squeeze maximum real estate from screen
    if self.rightVisibleColIndex == self.nVisibleCols-1:
        # try to move further left while right column is still full width
        while self.leftVisibleColIndex > 0:
            rightcol = self.visibleCols[self.rightVisibleColIndex]
            if (rightcol.width or 0) > self._visibleColLayout[self.rightVisibleColIndex][1]:
                # went too far
                self.cursorVisibleColIndex += 1
                self.leftVisibleColIndex += 1
                break
            else:
                self.cursorVisibleColIndex -= 1
                self.leftVisibleColIndex -= 1
                self.calcColLayout()  # recompute rightVisibleColIndex


@Sheet.api
def moveToNextRow(vs, func, reverse=False):
    'Move cursor to next (prev if reverse) row for which func returns True.  Returns False if no row meets the criteria.'
    rng = range(vs.cursorRowIndex-1, -1, -1) if reverse else range(vs.cursorRowIndex+1, vs.nRows)

    for i in rng:
        try:
            if func(vs.rows[i]):
                vs.cursorRowIndex = i
                return True
        except Exception:
            pass

    return False


@Sheet.api
def nextColRegex(sheet, colregex):
    'Go to first visible column after the cursor matching `colregex`.'
    pivot = sheet.cursorVisibleColIndex
    for i in itertools.chain(range(pivot+1, len(sheet.visibleCols)), range(0, pivot+1)):
        c = sheet.visibleCols[i]
        if re.search(colregex, c.name, sheet.regex_flags()):
            return i

    fail('no column name matches /%s/' % colregex)

Sheet.addCommand(None, 'go-left',  'cursorRight(-1)', 'go left'),
Sheet.addCommand(None, 'go-down',  'cursorDown(+1)', 'go down'),
Sheet.addCommand(None, 'go-up',    'cursorDown(-1)', 'go up'),
Sheet.addCommand(None, 'go-right', 'cursorRight(+1)', 'go right'),
Sheet.addCommand(None, 'go-pagedown', 'cursorDown(nScreenRows); sheet.topRowIndex += nScreenRows', 'scroll one page forward'),
Sheet.addCommand(None, 'go-pageup', 'cursorDown(-nScreenRows); sheet.topRowIndex -= nScreenRows', 'scroll one page backward'),

Sheet.addCommand(None, 'go-leftmost', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0', 'go all the way to the left of sheet'),
Sheet.addCommand(None, 'go-top', 'sheet.cursorRowIndex = sheet.topRowIndex = 0', 'go all the way to the top of sheet'),
Sheet.addCommand(None, 'go-bottom', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nScreenRows', 'go all the way to the bottom of sheet'),
Sheet.addCommand(None, 'go-rightmost', 'sheet.leftVisibleColIndex = len(visibleCols)-1; pageLeft(); sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go all the way to the right of sheet'),

@Sheet.command('BUTTON1_PRESSED', 'go-mouse', 'set cursor to row and column where mouse was clicked')
def go_mouse(sheet):
    ridx = sheet.visibleRowAtY(sheet.mouseY)
    if ridx is not None:
        sheet.cursorRowIndex = ridx
    cidx = sheet.visibleColAtX(sheet.mouseX)
    if cidx is not None:
        sheet.cursorVisibleColIndex = cidx

Sheet.addCommand(None, 'scroll-mouse', 'sheet.topRowIndex=cursorRowIndex-mouseY+1', 'scroll to mouse cursor location'),

Sheet.addCommand('BUTTON4_PRESSED', 'scroll-up', 'cursorDown(options.scroll_incr); sheet.topRowIndex += options.scroll_incr', 'scroll one row up'),
Sheet.addCommand('REPORT_MOUSE_POSITION', 'scroll-down', 'cursorDown(-options.scroll_incr); sheet.topRowIndex -= options.scroll_incr', 'scroll one row down'),

Sheet.addCommand('c', 'go-col-regex', 'sheet.cursorVisibleColIndex=nextColRegex(input("column name regex: ", type="regex-col", defaultLast=True))', 'go to next column with name matching regex')
Sheet.addCommand('zc', 'go-col-number', 'sheet.cursorVisibleColIndex = int(input("move to column number: "))', 'go to given column number (0-based)')
Sheet.addCommand('zr', 'go-row-number', 'sheet.cursorRowIndex = int(input("move to row number: "))', 'go to the given row number (0-based)')


Sheet.addCommand('<', 'go-prev-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorTypedValue: col.getTypedValue(row) != val, reverse=True) or status("no different value up this column")', 'go up current column to next value'),
Sheet.addCommand('>', 'go-next-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorTypedValue: col.getTypedValue(row) != val) or status("no different value down this column")', 'go down current column to next value'),
Sheet.addCommand('{', 'go-prev-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row), reverse=True) or status("no previous selected row")', 'go up current column to previous selected row'),
Sheet.addCommand('}', 'go-next-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row)) or status("no next selected row")', 'go down current column to next selected row'),

Sheet.addCommand('z<', 'go-prev-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row)), reverse=True) or status("no null down this column")', 'go up current column to next null value'),
Sheet.addCommand('z>', 'go-next-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row))) or status("no null down this column")', 'go down current column to next null value'),

for i in range(1, 11):
    globalCommand(ALT+str(i)[-1], 'jump-sheet-'+str(i), f'vd.push(*(list(s for s in allSheets if s.shortcut==str({i})) or fail("no sheet")))', f'jump to sheet {i}')

BaseSheet.bindkey('KEY_LEFT', 'go-left')
BaseSheet.bindkey('KEY_DOWN', 'go-down')
BaseSheet.bindkey('KEY_UP', 'go-up')
BaseSheet.bindkey('KEY_RIGHT', 'go-right')
BaseSheet.bindkey('KEY_HOME', 'go-leftmost')
BaseSheet.bindkey('KEY_END', 'go-rightmost')
BaseSheet.bindkey('KEY_NPAGE', 'go-pagedown')
BaseSheet.bindkey('KEY_PPAGE', 'go-pageup')

BaseSheet.bindkey('kHOM5', 'go-top')  # Ctrl+Home
BaseSheet.bindkey('KEY_EOL', 'go-bottom')  # Ctrl+End

BaseSheet.bindkey('gKEY_LEFT', 'go-leftmost'),
BaseSheet.bindkey('gKEY_RIGHT', 'go-rightmost'),
BaseSheet.bindkey('gKEY_UP', 'go-top'),
BaseSheet.bindkey('gKEY_DOWN', 'go-bottom'),

Sheet.bindkey('BUTTON1_CLICKED', 'go-mouse')
Sheet.bindkey('BUTTON3_PRESSED', 'go-mouse')

# vim-style scrolling with the 'z' prefix
Sheet.addCommand('zz', 'scroll-middle', 'sheet.topRowIndex = cursorRowIndex-int(nScreenRows/2)', 'scroll current row to center of screen')

Sheet.addCommand(None, 'go-right-page', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex', 'scroll cursor one page right')
Sheet.addCommand(None, 'go-left-page', 'pageLeft()', 'scroll cursor one page left')
Sheet.addCommand('zh', 'scroll-left', 'sheet.cursorVisibleColIndex -= options.scroll_incr', 'scroll one column left')
Sheet.addCommand('zl', 'scroll-right', 'sheet.cursorVisibleColIndex += options.scroll_incr', 'scroll one column right')
Sheet.addCommand(None, 'scroll-leftmost', 'sheet.leftVisibleColIndex = cursorVisibleColIndex', 'scroll sheet to leftmost column')
Sheet.addCommand(None, 'scroll-rightmost', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp', 'scroll sheet to rightmost column')

Sheet.addCommand(None, 'go-end',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to last row and last column')
Sheet.addCommand(None, 'go-home', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0', 'go to first row and first column')

BaseSheet.bindkey('CTRL-BUTTON4_PRESSED', 'scroll-left')
BaseSheet.bindkey('CTRL-REPORT_MOUSE_POSITION', 'scroll-right')

BaseSheet.bindkey('zk', 'scroll-up')
BaseSheet.bindkey('zj', 'scroll-down')
BaseSheet.bindkey('zKEY_UP', 'scroll-up')
BaseSheet.bindkey('zKEY_DOWN', 'scroll-down')
BaseSheet.bindkey('zKEY_LEFT', 'scroll-left')
BaseSheet.bindkey('zKEY_RIGHT', 'scroll-right')

# vim-like keybindings

BaseSheet.bindkey('h', 'go-left'),
BaseSheet.bindkey('j', 'go-down'),
BaseSheet.bindkey('k', 'go-up'),
BaseSheet.bindkey('l', 'go-right'),
BaseSheet.bindkey('^F', 'go-pagedown'),
BaseSheet.bindkey('^B', 'go-pageup'),
BaseSheet.bindkey('gg', 'go-top'),
BaseSheet.bindkey('G',  'go-bottom'),
BaseSheet.bindkey('gj', 'go-bottom'),
BaseSheet.bindkey('gk', 'go-top'),
BaseSheet.bindkey('gh', 'go-leftmost'),
BaseSheet.bindkey('gl', 'go-rightmost')

BaseSheet.addCommand('^^', 'jump-prev', 'vd.sheets[1:] or fail("no previous sheet"); vd.push(vd.sheets[1])', 'jump to previous sheet (swap with current sheet)')
