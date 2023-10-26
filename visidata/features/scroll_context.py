from visidata import vd, TableSheet

vd.option('disp_scroll_context', 0, 'number of lines of context to display above/below cursor when scrolling', max_help=1)


@TableSheet.after
def checkCursor(sheet):
    n = sheet.options.disp_scroll_context

    if sheet.cursorRowIndex-sheet.topRowIndex < n:
        sheet.topRowIndex = max(0, sheet.cursorRowIndex-n)

    if sheet.bottomRowIndex-sheet.cursorRowIndex < n:
        sheet.bottomRowIndex = sheet.cursorRowIndex+n
