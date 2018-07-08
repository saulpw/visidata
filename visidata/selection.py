from visidata import Sheet, Command

Sheet.commands.extend([
Command('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)'),
Command('s', 'select-row', 'select([cursorRow]); cursorDown(1)'),
Command('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)'),

Command('gt', 'toggle-rows', 'toggle(rows)'),
Command('gs', 'select-rows', 'select(rows)'),
Command('gu', 'unselect-rows', '_selectedRows.clear()'),

Command('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])'),
Command('zs', 'select-before', 'select(rows[:cursorRowIndex])'),
Command('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])'),
Command('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])'),
Command('gzs', 'select-after', 'select(rows[cursorRowIndex:])'),
Command('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])'),

Command('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))'),
Command('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))'),
Command('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))'),
Command('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))'),

Command(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorValue: c.getValue(r) == v), progress=False)'),
Command('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getValue(r) == c.getValue(currow) for c in vcols])), progress=False)'),


Command('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)'),
Command('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)')
])
