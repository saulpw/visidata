
from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('^Z', 's,i,r = clipboard.pop(); s.rows.insert(i, r)', 'undo last delete on original sheet')
globalCommand('^Z', '''
for s,i,r in vd.cliprows: s.rows.insert(i, r)
vd.cliprows.clear()
''', 'undo all deletes on clipboard')

globalCommand('y', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]', 'copies current row to clipboard')
globalCommand('d', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', 'deletes current row and moves to clipboard')
globalCommand('p', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'pastes clipboard rows after current row')

globalCommand('gd', 'vd.cliprows = list((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r)); deleteSelected()', 'deletes all selected rows and moves to clipboard')
globalCommand('gy', 'vd.cliprows = list((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r))', 'copies all selected rows to clipboard')

globalCommand('zy', 'vd.clipvalue = cursorDisplay', 'copies this cell to clipboard')
globalCommand('gzp', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)', 'sets contents of current column for selected rows to last clipboard value')
globalCommand('zp', 'cursorCol.setValue(cursorRow, vd.clipvalue)', 'sets contents of current column for current row to last clipboard value')

