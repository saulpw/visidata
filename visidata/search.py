from visidata import vd, Sheet, rotateRange, asyncthread

@Sheet.api
@asyncthread
def search_expr(sheet, expr, reverse=False):
    for i in rotateRange(len(sheet.rows), sheet.cursorRowIndex, reverse=reverse):
        try:
            if sheet.evalexpr(expr, sheet.rows[i]):
                sheet.cursorRowIndex=i
                return
        except Exception as e:
            vd.exceptionCaught(e)

    vd.fail(f'no {sheet.rowtype} where {expr}')

Sheet.addCommand('z/', 'search-expr', 'search_expr(inputExpr("search by expr: ") or fail("no expr"))', 'search by Python expression forwards in current column (with column names as variables)')
Sheet.addCommand('z?', 'searchr-expr', 'search_expr(inputExpr("searchr by expr: ") or fail("no expr"), reverse=True)', 'search by Python expression backwards in current column (with column names as variables)')
