from visidata import Sheet, asyncthread, Progress


@Sheet.api
@asyncthread
def select_equal_selected(sheet, col):
    selectedVals = set(col.getFullDisplayValue(row) for row in Progress(sheet.selectedRows))
    sheet.select(sheet.gatherBy(lambda r,c=col,vals=selectedVals: c.getFullDisplayValue(r) in vals), progress=False)


Sheet.addCommand('', 'select-equal-selected', 'select_equal_selected(cursorCol)', 'select rows with values in current column in already selected rows')
