from visidata import vd, TableSheet

vd.option('disp_scrolloff', 0, 'context lines to display above/below cursor when scrolling')

@TableSheet.api
def checkCursor(sheet):
    checkCursor.__wrapped__(sheet)

    disp_scrolloff = sheet.options.disp_scrolloff

    if sheet.cursorRowIndex-sheet.topRowIndex < disp_scrolloff:
        sheet.topRowIndex = max(0, sheet.cursorRowIndex-sheet.options.disp_scrolloff)

    if sheet.bottomRowIndex-sheet.cursorRowIndex < disp_scrolloff:
        sheet.bottomRowIndex = sheet.cursorRowIndex+disp_scrolloff
