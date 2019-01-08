from visidata import Sheet, undoSheetSelection

Sheet.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('s', 'select-row', 'selectRow(cursorRow); cursorDown(1)', undo=undoSheetSelection),
Sheet.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)', undo=undoSheetSelection),

Sheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)', undo=undoSheetSelection),
Sheet.addCommand('gs', 'select-rows', 'select(rows)', undo=undoSheetSelection),
Sheet.addCommand('gu', 'unselect-rows', '_selectedRows.clear()', undo=undoSheetSelection),

Sheet.addCommand('zt', 'stoggle-before', 'toggle(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zs', 'select-before', 'select(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('zu', 'unselect-before', 'unselect(rows[:cursorRowIndex])', undo=undoSheetSelection),
Sheet.addCommand('gzt', 'stoggle-after', 'toggle(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzs', 'select-after', 'select(rows[cursorRowIndex:])', undo=undoSheetSelection),
Sheet.addCommand('gzu', 'unselect-after', 'unselect(rows[cursorRowIndex:])', undo=undoSheetSelection),

Sheet.addCommand('|', 'select-col-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('\\', 'unselect-col-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))', undo=undoSheetSelection),
Sheet.addCommand('g|', 'select-cols-regex', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),
Sheet.addCommand('g\\', 'unselect-cols-regex', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))', undo=undoSheetSelection),

Sheet.addCommand(',', 'select-equal-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', undo=undoSheetSelection),

Sheet.addCommand('z|', 'select-expr', 'expr=inputExpr("select by expr: "); select(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection),
Sheet.addCommand('z\\', 'unselect-expr', 'expr=inputExpr("unselect by expr: "); unselect(gatherBy(lambda r, sheet=sheet, expr=expr: sheet.evalexpr(expr, r)), progress=False)', undo=undoSheetSelection)
