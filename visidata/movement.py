import itertools
import re

from visidata import vd, error, status, Sheet, Column, regex_flags, rotate_range


def nextColRegex(sheet, colregex):
    'Go to first visible column after the cursor matching `colregex`.'
    pivot = sheet.cursorVisibleColIndex
    for i in itertools.chain(range(pivot+1, len(sheet.visibleCols)), range(0, pivot+1)):
        c = sheet.visibleCols[i]
        if re.search(colregex, c.name, regex_flags()):
            return i

    error('no column name matches /%s/' % colregex)


# kwargs: regex=None, columns=None, backward=False
def searchRegex(sheet, moveCursor=False, reverse=False, **kwargs):
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

        regex = vd.searchContext.get("regex") or error("no regex")

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

vd.searchRegex = searchRegex
vd.searchContext = {}

def moveRegex(sheet, *args, **kwargs):
    list(searchRegex(sheet, *args, moveCursor=True, **kwargs))


Sheet.addCommand('c', 'go-col-regex', 'sheet.cursorVisibleColIndex=nextColRegex(sheet, input("column name regex: ", type="regex-col", defaultLast=True))')
Sheet.addCommand('r', 'search-keys', 'tmp=cursorVisibleColIndex; moveRegex(sheet, regex=input("row key regex: ", type="regex-row", defaultLast=True), columns=keyCols or [visibleCols[0]]); sheet.cursorVisibleColIndex=tmp')
Sheet.addCommand('zc', 'go-col-number', 'sheet.cursorVisibleColIndex = int(input("move to column number: "))')
Sheet.addCommand('zr', 'go-row-number', 'sheet.cursorRowIndex = int(input("move to row number: "))')

Sheet.addCommand('/', 'search-col', 'moveRegex(sheet, regex=input("/", type="regex", defaultLast=True), columns="cursorCol", backward=False)'),
Sheet.addCommand('?', 'searchr-col', 'moveRegex(sheet, regex=input("?", type="regex", defaultLast=True), columns="cursorCol", backward=True)'),
Sheet.addCommand('n', 'next-search', 'moveRegex(sheet, reverse=False)'),
Sheet.addCommand('N', 'prev-search', 'moveRegex(sheet, reverse=True)'),

Sheet.addCommand('g/', 'search-cols', 'moveRegex(sheet, regex=input("g/", type="regex", defaultLast=True), backward=False, columns="visibleCols")'),
Sheet.addCommand('g?', 'searchr-cols', 'moveRegex(sheet, regex=input("g?", type="regex", defaultLast=True), backward=True, columns="visibleCols")'),
