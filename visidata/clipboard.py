
from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('y', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]', 'copy current row to clipboard')
globalCommand('d', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', 'delete current row and move it to clipboard')
globalCommand('p', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row')
globalCommand('P', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row')

globalCommand('gd', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()', 'delete all selected rows and move them to clipboard')
globalCommand('gy', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows))', 'copy all selected rows to clipboard')

globalCommand('zy', 'vd.clipvalue = cursorDisplay', 'copy current cell to clipboard')
globalCommand('gzp', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)', 'set contents of current column for selected rows to last clipboard value')
globalCommand('zp', 'cursorCol.setValue(cursorRow, vd.clipvalue)', 'set contents of current column for current row to last clipboard value')

globalCommand('Y', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank current row to system clipboard')
globalCommand('gY', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank selected rows to system clipboard')
globalCommand('zY', 'copyToClipboard(cursorDisplay)', 'yank current value to system clipboard')

option('clipboard_copy_cmd', 'pbcopy w', 'command to copy stdin to system clipboard')
# or 'xsel --primary' for xsel
# or 'xclip -selection primary'
# or 'pbcopy w' for mac

import tempfile
import subprocess

def copyToClipboard(val):
    cmd = options.clipboard_copy_cmd or error('options.clipboard_copy_cmd not set')
    with tempfile.NamedTemporaryFile() as temp:
        with open(temp.name, 'w', encoding=options.encoding) as fp:
            fp.write(str(val))

        p = subprocess.Popen(cmd.split(), stdin=open(temp.name, 'r', encoding=options.encoding))
        p.communicate()
    status('copied value to clipboard')

def saveToClipboard(sheet, rows, filetype=None):
    cmd = options.clipboard_copy_cmd or error('options.clipboard_copy_cmd not set')
    vs = copy(sheet)
    vs.rows = rows
    filetype = filetype or options.filetype
    with tempfile.NamedTemporaryFile() as temp:
        tempfn = temp.name + "." + filetype
        saveSheet(vs, tempfn)
        sync()
        p = subprocess.Popen(cmd.split(), stdin=open(tempfn, 'r', encoding=options.encoding), close_fds=True)
        p.communicate()
    status('copied rows to clipboard')
