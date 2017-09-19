
from visidata import *

clipboard = []

globalCommand('B', 'vd.push(ClipboardSheet("clipboard", clipboard))', 'push clipboard sheet')

globalCommand('^Z', 's,i,r = clipboard.pop(); s.rows.insert(i, r)', 'undo last delete on original sheet')
globalCommand('g^Z', '''
for s,i,r in clipboard: s.rows.insert(i, r)
clipboard.clear()
''', 'undo all deletes on clipboard')

globalCommand('y', 'clipboard.append((sheet, cursorRowIndex, cursorRow))', 'copies current row and appends to clipboard')
globalCommand('d', 'clipboard.append((sheet, cursorRowIndex, rows.pop(cursorRowIndex)))', 'deletes current row and appends to clipboard')
globalCommand('p', 'rows.insert(cursorRowIndex+1, deepcopy(clipboard[-1][2])); cursorDown()', 'pastes most recent clipboard row after current row')

globalCommand('gd', 'clipboard.extend((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r)); deleteSelected()', 'deletes all selected rows and appends to clipboard')
globalCommand('gy', 'clipboard.extend((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r))', 'copies all selected rows and appends to clipboard')
globalCommand('gp', 'rows[cursorRowIndex+1:cursorRowIndex+2] = list(r for s,i,r in clipboard)', 'pastes all clipboard rows after current row')

globalCommand('zd', 'clipboard.append(cursorCol); columns.pop(cursorColIndex)', 'delete this column and move to clipboard')
globalCommand('zy', 'clipboard.append(cursorCol);', 'copy this column to clipboard')
globalCommand('zp', 'addColumn(clipboard.pop(), cursorColIndex+1)', 'paste column from clipboard')

globalCommand('zgd', 'for c in visibleCols: clipboard.append(c); columns.remove(c)', 'delete this column and move to clipboard')
globalCommand('zgy', 'clipboard.extend(columns);', 'copy all columns to clipboard')
globalCommand('zgp', 'columns.extend(clipboard); clipboard.clear(); recalc();', 'copy all columns to clipboard')

globalCommand('gzd', 'zgd')
globalCommand('gzy', 'zgy')
globalCommand('gzp', 'zgp')

#globalCommand('', 'rows.insert(cursorRowIndex, clipboard.pop())', 'pop last clipboard row and paste after cursor')

# ClipboardSheet row format: (source_sheet, source_row_idx, source_row)
class ClipboardSheet(Sheet):
    columns = [
        Column('source', getter=lambda r: r[0].name),
        Column('rownum', getter=lambda r: r[1]),
        Column('keys', getter=lambda r: ' '.join(c.getDisplayValue(r[2]) for c in r[0].keyCols)),
    ]
    def reload(self):
        self.rows = self.source
