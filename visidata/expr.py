from visidata import Progress, Sheet, Column, asyncthread, vd, ColumnExpr


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
    vd.status('set %d values = %s' % (len(rows), expr))


@Sheet.api
def inputExpr(self, prompt, *args, **kwargs):
    return vd.input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)


Sheet.addCommand('=', 'addcol-expr', 'addColumn(ColumnExpr(inputExpr("new column expr=")), index=cursorColIndex+1)', 'create new column from Python expression, with column names as variables')
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(selectedRows, inputExpr("set selected="))', 'set current column for selected rows to result of Python expression')
Sheet.addCommand('z=', 'setcell-expr', 'cursorCol.setValues([cursorRow], evalexpr(inputExpr("set expr="), cursorRow))', 'evaluate Python expression on current row and set current cell with result of Python expression')
Sheet.addCommand('gz=', 'setcol-iter', 'cursorCol.setValues(selectedRows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(selectedRows))))', 'set current column for selected rows to the items in result of Python sequence expression')

Sheet.addCommand(None, 'show-expr', 'status(evalexpr(inputExpr("show expr="), cursorRow))', 'evaluate Python expression on current row and show result on status line')
