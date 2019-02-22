import itertools
import re

from visidata import vd, VisiData, error, status, Sheet, Column, regex_flags, fail, Progress

__all__ = ['rotate_range']

vd.searchContext = {}  # [(regex, columns, backward)] -> kwargs from previous search

def rotate_range(n, idx, reverse=False):
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

Sheet.addCommand('<', 'prev-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val, reverse=True) or status("no different value up this column")'),
Sheet.addCommand('>', 'next-value', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val) or status("no different value down this column")'),
Sheet.addCommand('{', 'prev-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row), reverse=True) or status("no previous selected row")'),
Sheet.addCommand('}', 'next-selected', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row)) or status("no next selected row")'),

Sheet.addCommand('z<', 'prev-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row)), reverse=True) or status("no null down this column")'),
Sheet.addCommand('z>', 'next-null', 'moveToNextRow(lambda row,col=cursorCol,isnull=isNullFunc(): isnull(col.getValue(row))) or status("no null down this column")'),


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
        if re.search(colregex, c.name, regex_flags()):
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
            vd.searchContext["regex"] = re.compile(regex, regex_flags()) or error('invalid regex: %s' % regex)

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
        for r in rotate_range(len(sheet.rows), sheet.cursorRowIndex, reverse=searchBackward):
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
