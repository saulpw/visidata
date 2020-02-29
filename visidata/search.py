from visidata import Sheet, rotateRange


def evalmatcher(sheet, expr):
    def matcher(r):
        return sheet.evalexpr(expr, r)
    return matcher

def search_func(sheet, rows, func, reverse=False):
    for i in rotateRange(len(sheet.rows), sheet.cursorRowIndex, reverse=reverse):
        try:
            if func(sheet.rows[i]):
                return i
        except Exception:
            pass

Sheet.addCommand('z/', 'search-expr', 'sheet.cursorRowIndex=search_func(sheet, rows, evalmatcher(sheet, inputExpr("search by expr: "))) or status("no match")', 'search by Python expression forwards in current column (with column names as variables)')
Sheet.addCommand('z?', 'searchr-expr', 'sheet.cursorRowIndex=search_func(sheet, rows, evalmatcher(sheet, inputExpr("search by expr: ")), reverse=True) or status("no match")', 'search by Python expression backwards in current column (with column names as variables)')
