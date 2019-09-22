import itertools
import re

from visidata import vd, VisiData, error, status, BaseSheet, Sheet, Column, fail, Progress, globalCommand, ALT

__all__ = ['rotateRange']

VisiData.init('searchContext', dict) # [(regex, columns, backward)] -> kwargs from previous search

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
            if rightcol.width > self.visibleColLayout[self.rightVisibleColIndex][1]:
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


@VisiData.api
def moveRegex(vd, sheet, *args, **kwargs):
    list(vd.searchRegex(sheet, *args, moveCursor=True, **kwargs))


# kwargs: regex=None, columns=None, backward=False
@VisiData.api
def searchRegex(vd, sheet, moveCursor=False, reverse=False, **kwargs):
        'Set row index if moveCursor, otherwise return list of row indexes.'
        def findMatchingColumn(sheet, row, columns, func):
            'Find column for which func matches the displayed value in this row'
            for c in columns:
                if func(c.getDisplayValue(row)):
                    return c

        vd.searchContext.update(kwargs)

        regex = kwargs.get("regex")
        if regex:
            vd.searchContext["regex"] = re.compile(regex, sheet.regex_flags()) or error('invalid regex: %s' % regex)

        regex = vd.searchContext.get("regex") or fail("no regex")

        columns = vd.searchContext.get("columns")
        if columns == "cursorCol":
            columns = [sheet.cursorCol]
        elif columns == "visibleCols":
            columns = tuple(sheet.visibleCols)
        elif isinstance(columns, Column):
            columns = [columns]

        if not columns:
            error('bad columns')

        searchBackward = vd.searchContext.get("backward")
        if reverse:
            searchBackward = not searchBackward

        matchingRowIndexes = 0
        for r in rotateRange(len(sheet.rows), sheet.cursorRowIndex, reverse=searchBackward):
            c = findMatchingColumn(sheet, sheet.rows[r], columns, regex.search)
            if c:
                if moveCursor:
                    sheet.cursorRowIndex = r
                    sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)
                    return
                else:
                    matchingRowIndexes += 1
                    yield r

        status('%s matches for /%s/' % (matchingRowIndexes, regex.pattern))


Sheet.addCommand(None, 'go-left',  'cursorRight(-1)'),
Sheet.addCommand(None, 'go-down',  'cursorDown(+1)'),
Sheet.addCommand(None, 'go-up',    'cursorDown(-1)'),
Sheet.addCommand(None, 'go-right', 'cursorRight(+1)'),
Sheet.addCommand(None, 'go-pagedown', 'cursorDown(nScreenRows); sheet.topRowIndex += nScreenRows'),
Sheet.addCommand(None, 'go-pageup', 'cursorDown(-nScreenRows); sheet.topRowIndex -= nScreenRows'),

Sheet.addCommand(None, 'go-leftmost', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0'),
Sheet.addCommand(None, 'go-top', 'sheet.cursorRowIndex = sheet.topRowIndex = 0'),
Sheet.addCommand(None, 'go-bottom', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nScreenRows'),
Sheet.addCommand(None, 'go-rightmost', 'sheet.leftVisibleColIndex = len(visibleCols)-1; pageLeft(); sheet.cursorVisibleColIndex = len(visibleCols)-1'),

Sheet.addCommand('BUTTON1_PRESSED', 'go-mouse', 'sheet.cursorRowIndex=visibleRowAtY(mouseY) or sheet.cursorRowIndex; sheet.cursorVisibleColIndex=visibleColAtX(mouseX) or sheet.cursorVisibleColIndex'),

Sheet.addCommand('BUTTON1_RELEASED', 'scroll-mouse', 'sheet.topRowIndex=cursorRowIndex-mouseY+1'),

Sheet.addCommand('BUTTON4_PRESSED', 'scroll-up', 'cursorDown(options.scroll_incr); sheet.topRowIndex += options.scroll_incr'),
Sheet.addCommand('REPORT_MOUSE_POSITION', 'scroll-down', 'cursorDown(-options.scroll_incr); sheet.topRowIndex -= options.scroll_incr'),

Sheet.addCommand('c', 'go-col-regex', 'sheet.cursorVisibleColIndex=nextColRegex(input("column name regex: ", type="regex-col", defaultLast=True))')
Sheet.addCommand('r', 'search-keys', 'tmp=cursorVisibleColIndex; vd.moveRegex(sheet, regex=input("row key regex: ", type="regex-row", defaultLast=True), columns=keyCols or [visibleCols[0]]); sheet.cursorVisibleColIndex=tmp')
Sheet.addCommand('zc', 'go-col-number', 'sheet.cursorVisibleColIndex = int(input("move to column number: "))')
Sheet.addCommand('zr', 'go-row-number', 'sheet.cursorRowIndex = int(input("move to row number: "))')

Sheet.addCommand('/', 'search-col', 'vd.moveRegex(sheet, regex=input("/", type="regex", defaultLast=True), columns="cursorCol", backward=False)'),
Sheet.addCommand('?', 'searchr-col', 'vd.moveRegex(sheet, regex=input("?", type="regex", defaultLast=True), columns="cursorCol", backward=True)'),
Sheet.addCommand('n', 'next-search', 'vd.moveRegex(sheet, reverse=False)'),
Sheet.addCommand('N', 'prev-search', 'vd.moveRegex(sheet, reverse=True)'),

Sheet.addCommand('g/', 'search-cols', 'vd.moveRegex(sheet, regex=input("g/", type="regex", defaultLast=True), backward=False, columns="visibleCols")'),
Sheet.addCommand('g?', 'searchr-cols', 'vd.moveRegex(sheet, regex=input("g?", type="regex", defaultLast=True), backward=True, columns="visibleCols")'),

Sheet.addCommand('<', 'prev-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorTypedValue: col.getTypedValue(row) != val, reverse=True) or status("no different value up this column")'),
Sheet.addCommand('>', 'next-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorTypedValue: col.getTypedValue(row) != val) or status("no different value down this column")'),
Sheet.addCommand('{', 'prev-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row), reverse=True) or status("no previous selected row")'),
Sheet.addCommand('}', 'next-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row)) or status("no next selected row")'),

Sheet.addCommand('z<', 'prev-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row)), reverse=True) or status("no null down this column")'),
Sheet.addCommand('z>', 'next-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row))) or status("no null down this column")'),

for i in range(1, 11):
    globalCommand(ALT+str(i)[-1], 'jump-sheet-'+str(i), 'vd.allSheets[%s:] or fail("no sheet"); vd.push(vd.allSheets[%s])' % (i-1, i-1))

BaseSheet.bindkey('KEY_LEFT', 'go-left')
BaseSheet.bindkey('KEY_DOWN', 'go-down')
BaseSheet.bindkey('KEY_UP', 'go-up')
BaseSheet.bindkey('KEY_RIGHT', 'go-right')
BaseSheet.bindkey('KEY_HOME', 'go-top')
BaseSheet.bindkey('KEY_END', 'go-bottom')
BaseSheet.bindkey('KEY_NPAGE', 'go-pagedown')
BaseSheet.bindkey('KEY_PPAGE', 'go-pageup')

BaseSheet.bindkey('gKEY_LEFT', 'go-leftmost'),
BaseSheet.bindkey('gKEY_RIGHT', 'go-rightmost'),
BaseSheet.bindkey('gKEY_UP', 'go-top'),
BaseSheet.bindkey('gKEY_DOWN', 'go-bottom'),

Sheet.bindkey('BUTTON1_CLICKED', 'go-mouse')
Sheet.bindkey('BUTTON3_PRESSED', 'go-mouse')

# vim-style scrolling with the 'z' prefix
Sheet.addCommand('zz', 'scroll-middle', 'sheet.topRowIndex = cursorRowIndex-int(nScreenRows/2)')

Sheet.addCommand(None, 'page-right', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = rightVisibleColIndex')
Sheet.addCommand(None, 'page-left', 'pageLeft()')
Sheet.addCommand('zh', 'scroll-left', 'sheet.cursorVisibleColIndex -= options.scroll_incr')
Sheet.addCommand('zl', 'scroll-right', 'sheet.cursorVisibleColIndex += options.scroll_incr')
Sheet.addCommand(None, 'scroll-leftmost', 'sheet.leftVisibleColIndex = cursorVisibleColIndex')
Sheet.addCommand(None, 'scroll-rightmost', 'tmp = cursorVisibleColIndex; pageLeft(); sheet.cursorVisibleColIndex = tmp')

Sheet.addCommand(None, 'go-end',  'sheet.cursorRowIndex = len(rows)-1; sheet.cursorVisibleColIndex = len(visibleCols)-1')
Sheet.addCommand(None, 'go-home', 'sheet.topRowIndex = sheet.cursorRowIndex = 0; sheet.leftVisibleColIndex = sheet.cursorVisibleColIndex = 0')

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

BaseSheet.addCommand('^^', 'prev-sheet', 'vd.sheets[1:] or fail("no previous sheet"); vd.push(vd.sheets[1])')
