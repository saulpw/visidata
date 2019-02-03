from visidata import Progress, status, Column, asyncthread


@Column.api
@asyncthread
def setValuesFromExpr(self, rows, expr):
    compiledExpr = compile(expr, '<expr>', 'eval')
    for row in Progress(rows, 'setting'):
        self.setValueSafe(row, self.sheet.evalexpr(compiledExpr, row))
    self.recalc()
    status('set %d values = %s' % (len(rows), expr))
