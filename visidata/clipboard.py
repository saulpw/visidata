
from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('y', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]', 'copy current row to clipboard', 'data-clipboard-copy-row')
globalCommand('d', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', 'delete current row and move it to clipboard', 'modify-delete-row')
globalCommand('p', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row', 'data-clipboard-paste-after')
globalCommand('P', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row', 'data-clipboard-paste-before')

globalCommand('gd', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()', 'delete selected rows and move them to clipboard', 'modify-delete-selected')
globalCommand('gy', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows))', 'copy selected rows to clipboard', 'data-clipboard-copy-selected')

globalCommand('zy', 'vd.clipvalue = cursorDisplay', 'copy current cell to clipboard', 'data-clipboard-copy-cell')
globalCommand('gzp', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)', 'set contents of current column for selected rows to last clipboard value', 'data-clipboard-paste-selected')
globalCommand('zp', 'cursorCol.setValue(cursorRow, vd.clipvalue)', 'set contents of current column for current row to last clipboard value', 'data-clipboard-paste-cell')

globalCommand('Y', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank (copy) current row to system clipboard', 'data-clipboard-copy-system-row')
globalCommand('gY', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank (copy) selected rows to system clipboard', 'data-clipboard-copy-system-selected')
globalCommand('zY', 'copyToClipboard(cursorDisplay)', 'yank (copy) current cell to system clipboard', 'data-clipboard-copy-system-cell')

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

@async
def saveToClipboard(sheet, rows, filetype=None):
    cmd = options.clipboard_copy_cmd or error('options.clipboard_copy_cmd not set')
    vs = copy(sheet)
    vs.rows = rows
    filetype = filetype or options.filetype
    with tempfile.NamedTemporaryFile() as temp:
        tempfn = temp.name + "." + filetype
        status('copying rows to clipboard')
        saveSheet(vs, tempfn)
        sync(1)
        p = subprocess.Popen(cmd.split(), stdin=open(tempfn, 'r', encoding=options.encoding), close_fds=True)
        p.communicate()
    status('done')
