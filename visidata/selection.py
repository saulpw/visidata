from visidata import Sheet

Sheet.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)'),
Sheet.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)'),
Sheet.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)'),

Sheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)'),
Sheet.addCommand('gs', 'select-rows', 'select(rows)'),
Sheet.addCommand('gu', 'unselect-rows', '_selectedRows.clear()'),

Sheet.addCommand('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])'),
Sheet.addCommand('zs', 'select-before', 'select(rows[:cursorRowIndex])'),
Sheet.addCommand('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])'),
Sheet.addCommand('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])'),
Sheet.addCommand('gzs', 'select-after', 'select(rows[cursorRowIndex:])'),
Sheet.addCommand('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])'),

Sheet.addCommand('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))'),
Sheet.addCommand('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))'),
Sheet.addCommand('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))'),
Sheet.addCommand('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))'),

Sheet.addCommand(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)'),
Sheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)'),

Sheet.addCommand('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)'),
Sheet.addCommand('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)')
