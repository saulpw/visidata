
from visidata import *

clipboard = []

command('^Z', 's,i,r = clipboard.pop(); s.rows.insert(i, r)', 'undo last delete on original sheet')
command('g^Z', '''
for s,i,r in clipboard: s.rows.insert(i, r)
clipboard.clear()
''', 'undo all deletes on clipboard')

command('y', 'clipboard.append((sheet, cursorRowIndex, cursorRow))', 'yank (copy) this row to clipboard')
command('d', 'clipboard.append((sheet, cursorRowIndex, rows.pop(cursorRowIndex)))', 'delete (cut) this row and move to clipboard')
command('p', 'rows.insert(cursorRowIndex+1, clipboard[-1][2]); cursorDown()', 'paste last clipboard row after cursor on this sheet')

command('gd', 'clipboard.extend((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r)); deleteSelected()', 'delete (cut) all selected rows and move to clipboard')
command('gy', 'clipboard.extend((sheet, i, r) for i, r in enumerate(rows) if sheet.isSelected(r))', 'yank (copy) all selected rows to clipboard')
command('gp', 'rows[cursorRowIndex+1:cursorRowIndex+2] = list(r for s,i,r in clipboard)', 'paste all clipboard rows after cursor on this sheet')

command('B', 'vd.push(ClipboardSheet("clipboard", clipboard))', 'push clipboard sheet')

#command('', 'rows.insert(cursorRowIndex, clipboard.pop())', 'pop last clipboard row and paste after cursor')

class ClipboardSheet(Sheet):
    def reload(self):
        self.columns = [
            Column('source', getter=lambda r: r[0].name),
            Column('rownum', getter=lambda r: r[1]),
            Column('keys', getter=lambda r: ' '.join(c.getDisplayValue(r[2]) for c in r[0].keyCols)),
        ]
        self.rows = self.source
