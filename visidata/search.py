import re
from visidata import vd, VisiData, BaseSheet, Sheet, Column, Progress, asyncthread, rotateRange

VisiData.init('searchContext', dict) # [(regex, columns, backward)] -> kwargs from previous search

vd.help_regex_flags = '''# Regex Flags Help
- `A` (ASCII) ASCII-only matching (not unicode)
- `I` (IGNORECASE): case-insensitive matching
- `M` (MULTILINE): `^` and `$` match after/before newlines
- `S` (DOTALL): `.` match any character at all, including newline
- `X` (VERBOSE): allow verbose regex
'''


@VisiData.api
@asyncthread
def moveRegex(vd, sheet, *args, **kwargs):
    list(vd.searchRegex(sheet, *args, moveCursor=True, **kwargs))


# kwargs: regex=None, columns=None, backward=False
@VisiData.api
def searchRegex(vd, sheet, moveCursor=False, reverse=False, regex_flags=None, **kwargs):
        'Set row index if moveCursor, otherwise return list of row indexes.'
        def findMatchingColumn(sheet, row, columns, func):
            'Find column for which func matches the displayed value in this row'
            for c in columns:
                if func(c.getDisplayValue(row)):
                    return c

        vd.searchContext.update(kwargs)

        regex = kwargs.get("regex")
        if regex:
            if regex_flags is None:
                regex_flags = sheet.options.regex_flags  # regex_flags defined in features.regex
            flagbits = sum(getattr(re, f.upper()) for f in regex_flags)
            try:
                compiled_re = re.compile(regex, flagbits)
                vd.searchContext["regex"] = compiled_re
            except re.error as e:
                vd.searchContext["regex"] = None  # make future calls to search-next fail
                vd.error('invalid regex: %s' % e.msg)

        regex = vd.searchContext.get("regex") or vd.fail("no regex")

        columns = vd.searchContext.get("columns")
        if columns == "cursorCol":
            columns = [sheet.cursorCol]
        elif columns == "visibleCols":
            columns = tuple(sheet.visibleCols)
        elif isinstance(columns, Column):
            columns = [columns]

        if not columns:
            vd.error('bad columns')

        searchBackward = vd.searchContext.get("backward")
        if reverse:
            searchBackward = not searchBackward

        matchingRowIndexes = 0
        for rowidx in rotateRange(len(sheet.rows), sheet.cursorRowIndex, reverse=searchBackward):
            c = findMatchingColumn(sheet, sheet.rows[rowidx], columns, regex.search)
            if c:
                if moveCursor:
                    sheet.cursorRowIndex = rowidx
                    sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)
                    return
                else:
                    matchingRowIndexes += 1
                    yield rowidx

        if kwargs.get('printStatus', True):
            vd.status('%s matches for /%s/' % (matchingRowIndexes, regex.pattern))


@Sheet.api
def searchInputRegex(sheet, action:str, columns:str='cursorCol'):
    r = vd.inputMultiple(regex=dict(prompt=f"{action} regex: ", type="regex", defaultLast=True, help=vd.help_regex),
                         flags=dict(prompt="regex flags: ", type="regex_flags", value=sheet.options.regex_flags, help=vd.help_regex_flags))

    return vd.searchRegex(sheet, regex=r['regex'], regex_flags=r['flags'], columns=columns)

@Sheet.api
def moveInputRegex(sheet, action:str, type="regex", **kwargs):
    r = vd.inputMultiple(regex=dict(prompt=f"{action} regex: ", type=type, defaultLast=True, help=vd.help_regex),
                         flags=dict(prompt="regex flags: ", type="regex_flags", value=sheet.options.regex_flags, help=vd.help_regex_flags))

    return vd.moveRegex(sheet, regex=r['regex'], regex_flags=r['flags'], **kwargs)

@Sheet.api
@asyncthread
def search_expr(sheet, expr, reverse=False, curcol=None):
    for i in rotateRange(len(sheet.rows), sheet.cursorRowIndex, reverse=reverse):
        try:
            if sheet.evalExpr(expr, sheet.rows[i], curcol=curcol):
                sheet.cursorRowIndex=i
                return
        except Exception as e:
            vd.exceptionCaught(e)

    vd.fail(f'no {sheet.rowtype} where {expr}')


Sheet.addCommand('r', 'search-keys', 'tmp=cursorVisibleColIndex; moveInputRegex("row key", type="regex-row", columns=keyCols or [visibleCols[0]]); sheet.cursorVisibleColIndex=tmp', 'go to next row with key matching regex')
Sheet.addCommand('/', 'search-col', 'moveInputRegex("search", columns="cursorCol", backward=False)', 'search for regex forwards in current column')
Sheet.addCommand('?', 'searchr-col', 'moveInputRegex("reverse search", columns="cursorCol", backward=True)', 'search for regex backwards in current column')
Sheet.addCommand('n', 'search-next', 'vd.moveRegex(sheet, reverse=False)', 'go to next match from last regex search')
Sheet.addCommand('N', 'searchr-next', 'vd.moveRegex(sheet, reverse=True)', 'go to previous match from last regex search')

Sheet.addCommand('g/', 'search-cols', 'moveInputRegex("g/", backward=False, columns="visibleCols")', 'search for regex forwards over all visible columns')
Sheet.addCommand('g?', 'searchr-cols', 'moveInputRegex("g?", backward=True, columns="visibleCols")', 'search for regex backwards over all visible columns')
Sheet.addCommand('z/', 'search-expr', 'search_expr(inputExpr("search by expr: ") or fail("no expr"), curcol=cursorCol)', 'search by Python expression forwards in current column (with column names as variables)')
Sheet.addCommand('z?', 'searchr-expr', 'search_expr(inputExpr("searchr by expr: ") or fail("no expr"), curcol=cursorCol, reverse=True)', 'search by Python expression backwards in current column (with column names as variables)')

vd.addMenuItems('''
    View > Search > current column > search-col
    View > Search > visible columns > search-cols
    View > Search > key columns > search-keys
    View > Search > by Python expr > search-expr
    View > Search > again > search-next
    View > Search backward > current column > searchr-col
    View > Search backward > visible columns > searchr-cols
    View > Search backward > by Python expr > searchr-expr
    View > Search backward > again > searchr-next
''')
