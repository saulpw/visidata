import itertools
import re
from visidata import vd, Sheet, AttrDict, dispwidth


@Sheet.api
def nextColRegex(sheet, colregex):
    'Go to first visible column after the cursor matching `colregex`.'
    pivot = sheet.cursorVisibleColIndex
    for i in itertools.chain(range(pivot+1, len(sheet.visibleCols)), range(0, pivot+1)):
        c = sheet.visibleCols[i]
        if re.search(colregex, c.name, sheet.regex_flags()):
            return i

    vd.fail('no column name matches /%s/' % colregex)

@Sheet.api
def nextColName(sheet, show_cells=True):
    if len(sheet.visibleCols) == 0: vd.fail('no columns to choose from')

    prompt = 'choose column name: '
    colnames = []
    for c in sheet.visibleCols:
        dv = None
        if show_cells and len(sheet.rows) > 0:
            dv = c.getDisplayValue(sheet.cursorRow)
        #the underscore that starts _cursor_cell excludes it from being fuzzy matched
        item = AttrDict(name_lower=c.name.lower(),
                        name=c.name,
                        _cursor_cell=dv)
        colnames.append(item)

    def _fmt_colname(match, row, trigger_key):
        name = match.formatted.get('name', row.name) if match else row.name
        r = ' '*(len(prompt)-3)
        r += f'[:keystrokes]{trigger_key}[/]  '
        if show_cells and len(sheet.rows) > 0:
            # pad the right side with spaces
            # use row.name, because name from match contains
            # extra formatting characters that change its length
            n_spaces = max(20 - dispwidth(row.name), 0)
            r += name + n_spaces*' '
            r += '   '
            #todo:  does not show disp_note_none for None
            r += row._cursor_cell
        else:
            r += name
        return r
    name = vd.activeSheet.inputPalette(prompt,
            colnames,
            value_key='name',
            type='column_name',
            formatter=_fmt_colname)

    pivot = sheet.cursorVisibleColIndex
    for i in itertools.chain(range(pivot+1, len(sheet.visibleCols)), range(0, pivot+1)):
        if name == sheet.visibleCols[i].name:
            return i

    vd.warning(f'found no column with name: {name}')


Sheet.addCommand('c', 'go-col-regex', 'sheet.cursorVisibleColIndex=nextColRegex(inputRegex("column name regex: ", type="regex-col", defaultLast=True))', 'go to next column with name matching regex')
Sheet.addCommand('zc', 'go-col-number', 'sheet.cursorVisibleColIndex = int(input("move to column number: "))', 'go to given column number (0-based)')
Sheet.addCommand('', 'go-col-name', 'sheet.cursorVisibleColIndex=nextColName()', 'go to next column with name matching string, case-insensitive')

vd.addMenuItems('''
    Column > Goto > by regex > go-col-regex
    Column > Goto > by number > go-col-number
    Column > Goto > by name > go-col-name
''')
