from visidata import Progress, status, Sheet, Column, asyncthread, vd, undoAddCols, undoEditCells
from visidata import EscapeException, fail, VisiData, ColumnExpr, options, option

option('evalexpr_live', True, 'eval expr while being input')


class CompleteExpr:
    def __init__(self, sheet=None):
        self.sheet = sheet

    def __call__(self, val, state):
        i = len(val)-1
        while val[i:].isidentifier() and i >= 0:
            i -= 1

        if i < 0:
            base = ''
            partial = val
        elif val[i] == '.':  # no completion of attributes
            return None
        else:
            base = val[:i+1]
            partial = val[i+1:]

        varnames = []
        varnames.extend(sorted((base+col.name) for col in self.sheet.columns if col.name.startswith(partial)))
        varnames.extend(sorted((base+x) for x in globals() if x.startswith(partial)))
        return varnames[state%len(varnames)]


@Column.api
@asyncthread
def setValuesFromExpr(self, rows, expr):
    compiledExpr = compile(expr, '<expr>', 'eval')
    for row in Progress(rows, 'setting'):
        self.setValueSafe(row, self.sheet.evalexpr(compiledExpr, row))
    self.recalc()
    status('set %d values = %s' % (len(rows), expr))


@Sheet.api
def inputExpr(self, prompt, *args, **kwargs):
    return vd.input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)


@Column.api
def updateExpr(col, val):
    col.name = val
    col.expr = val
    col.sheet.draw(vd.scr)


@VisiData.api
def addcol_expr(vd, sheet, colidx):
    if not options.evalexpr_live:
        return sheet.addColumn(ColumnExpr(sheet.inputExpr("new column expr=")), index=colidx)

    try:
        c = sheet.addColumn(ColumnExpr("", width=options.default_width), index=colidx)
        oldidx = sheet.cursorVisibleColIndex
        sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)

        expr = sheet.editCell(sheet.cursorVisibleColIndex, -1,
                                completer=CompleteExpr(sheet),
                                updater=lambda val,col=c: col.updateExpr(val))

        c.expr = expr or fail("no expr")
        c.width = None
    except (Exception, EscapeException):
        sheet.columns.remove(c)
        sheet.cursorVisibleColIndex = oldidx
        raise


Sheet.addCommand('=', 'addcol-expr', 'addcol_expr(sheet, cursorColIndex+1)', undo=undoAddCols)
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(selectedRows or rows, inputExpr("set selected="))', undo=undoEditCells)
