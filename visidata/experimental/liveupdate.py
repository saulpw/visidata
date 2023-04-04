from visidata import Column, vd, ColumnExpr, CompleteExpr, EscapeException, Sheet


@Column.api
def updateExpr(col, val):
    col.name = val
    try:
        col.expr = val
    except SyntaxError:
        col.expr = None

    col.sheet.draw(col.sheet._scr)


@Column.api  # expr.setter
def expr(self, expr):
    try:
        self.compiledExpr = compile(expr, '<expr>', 'eval') if expr else None
        self._expr = expr
    except SyntaxError as e:
        self._expr = None


@Sheet.api
def addcol_expr(sheet):
    try:
        c = sheet.addColumnAtCursor(ColumnExpr("", width=sheet.options.default_width))
        oldidx = sheet.cursorVisibleColIndex
        sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)

        expr = sheet.editCell(sheet.cursorVisibleColIndex, -1,
                                completer=CompleteExpr(sheet),
                                updater=lambda val,col=c: col.updateExpr(val))

        c.expr = expr or vd.fail("no expr")
        c.name = expr
        c.width = None
    except (Exception, EscapeException):
        sheet.columns.remove(c)
        sheet.cursorVisibleColIndex = oldidx
        raise


Sheet.addCommand(None, 'addcol-expr', 'sheet.addcol_expr()', "create new column from Python expression, updating the column's calculated values live")
Sheet.addCommand(None, 'addcol-new', 'c=addColumnAtIndex(SettableColumn(width=options.default_width)); draw(sheet._scr); cursorVisibleColIndex=visibleCols.index(c); c.name=editCell(cursorVisibleColIndex, -1); c.width=None', 'append new column, updating the column name live')
