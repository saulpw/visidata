from visidata import Progress, status, Sheet, Column, asyncthread, vd, ColumnExpr


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
    vd.addUndoSetValues([self], rows)
    for row in Progress(rows, 'setting'):
        self.setValueSafe(row, self.sheet.evalexpr(compiledExpr, row))
    self.recalc()
    status('set %d values = %s' % (len(rows), expr))


@Sheet.api
def inputExpr(self, prompt, *args, **kwargs):
    return vd.input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)


Sheet.addCommand('=', 'addcol-expr', 'addColumn(ColumnExpr(inputExpr("new column expr=")), index=cursorColIndex+1)')
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(selectedRows, inputExpr("set selected="))')
Sheet.addCommand('z=', 'setcell-expr', 'cursorCol.setValues([cursorRow], evalexpr(inputExpr("set expr="), cursorRow))')
