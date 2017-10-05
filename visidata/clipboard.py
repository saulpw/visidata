
from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('y', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]', 'copy current row to clipboard')
globalCommand('d', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', 'delete current row and move it to clipboard')
globalCommand('p', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row')

globalCommand('gd', 'vd.cliprows = list((sheet, i, r) for i, r in enumerate(selectedRows)); deleteSelected()', 'delete all selected rows and move them to clipboard')
globalCommand('gy', 'vd.cliprows = list((sheet, i, r) for i, r in enumerate(selectedRows))', 'copy all selected rows to clipboard')

globalCommand('zy', 'vd.clipvalue = cursorDisplay', 'copy this cell to clipboard')
globalCommand('gzp', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)', 'set contents of current column for selected rows to last clipboard value')
globalCommand('zp', 'cursorCol.setValue(cursorRow, vd.clipvalue)', 'set contents of current column for current row to last clipboard value')

