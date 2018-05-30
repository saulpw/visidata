from visidata import Sheet, Command

Sheet.commands.extend([
Command('t', 'toggle([cursorRow]); cursorDown(1)', 'toggle selection of current row', 'rows-toggle-current'),
Command('s', 'select([cursorRow]); cursorDown(1)', 'select current row', 'rows-select-current'),
Command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect current row', 'rows-unselect-current'),

Command('|', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))', 'select rows matching regex in current column', 'rows-select-regex'),
Command('\\', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))', 'unselect rows matching regex in current column', 'rows-unselect-regex'),

Command('gt', 'toggle(rows)', 'toggle selection of all rows', 'rows-toggle-all'),
Command('gs', 'select(rows)', 'select all rows', 'rows-select-all'),
Command('gu', '_selectedRows.clear()', 'unselect all rows', 'rows-unselect-all'),

Command('zt', 'toggle(rows[:cursorRowIndex])', 'toggle select rows from top to cursor', 'rows-toggle-to-cursor'),
Command('zs', 'select(rows[:cursorRowIndex])', 'select all rows from top to cursor', 'rows-select-to-cursor'),
Command('zu', 'unselect(rows[:cursorRowIndex])', 'unselect all rows from top to cursor', 'rows-unselect-to-cursor'),
Command('gzt', 'toggle(rows[cursorRowIndex:])', 'toggle select rows from cursor to bottom', 'rows-toggle-from-cursor'),
Command('gzs', 'select(rows[cursorRowIndex:])', 'select all rows from cursor to bottom', 'rows-select-from-cursor'),
Command('gzu', 'unselect(rows[cursorRowIndex:])', 'unselect all rows from cursor to bottom', 'rows-unselect-from-cursor'),

Command('|', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))', 'select rows matching regex in current column', 'rows-select-regex'),
Command('\\', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))', 'unselect rows matching regex in current column', 'rows-unselect-regex'),
Command('g|', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))', 'select rows matching regex in any visible column', 'rows-select-regex-all'),
Command('g\\', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))', 'unselect rows matching regex in any visible column', 'rows-unselect-regex-all'),

Command(',', 'select(gatherBy(lambda r,c=cursorCol,v=cursorValue: c.getValue(r) == v), progress=False)', 'select rows matching current cell in current column', 'rows-select-like-cell'),
Command('g,', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getValue(r) == c.getValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns', 'rows-select-like-row'),


Command('z|', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', 'select rows with a Python expression', 'rows-select-expr'),
Command('z\\', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', 'unselect rows with a Python expression', 'rows-unselect-expr')
])
