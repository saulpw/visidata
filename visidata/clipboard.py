import shutil
import subprocess
import tempfile

from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('y', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]', 'copy current row to clipboard', 'data-clipboard-copy-row')
globalCommand('d', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', 'delete current row and move it to clipboard', 'modify-delete-row')
globalCommand('p', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row', 'data-clipboard-paste-after')
globalCommand('P', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)', 'paste clipboard rows after current row', 'data-clipboard-paste-before')

globalCommand('gd', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()', 'delete selected rows and move them to clipboard', 'modify-delete-selected')
globalCommand('gy', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); status("%d %s to clipboard" % (len(vd.cliprows), rowtype))', 'copy selected rows to clipboard', 'data-clipboard-copy-selected')

globalCommand('zy', 'vd.clipvalue = cursorDisplay', 'copy current cell to clipboard', 'data-clipboard-copy-cell')
globalCommand('gzp', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)', 'set contents of current column for selected rows to last clipboard value', 'data-clipboard-paste-selected')
globalCommand('zp', 'cursorCol.setValue(cursorRow, vd.clipvalue)', 'set contents of current column for current row to last clipboard value', 'data-clipboard-paste-cell')

globalCommand('Y', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank (copy) current row to system clipboard', 'data-clipboard-copy-system-row')
globalCommand('gY', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.filetype or "csv"))', 'yank (copy) selected rows to system clipboard', 'data-clipboard-copy-system-selected')
globalCommand('zY', 'copyToClipboard(cursorDisplay)', 'yank (copy) current cell to system clipboard', 'data-clipboard-copy-system-cell')

option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard')

commands = {
    'clip': [],                                       # Windows Vista+
    'pbcopy': ['w'],                                  # macOS
    'xclip': ['-selection', 'clipboard', '-filter'],  # Linux etc.
    'xsel': ['--clipboard', '--input'],               # Linux etc.
}


class _Clipboard:
    'Cross-platform helper to copy a cell or multiple rows to the system clipboard.'

    def __init__(self, custom_command):
        if custom_command:
            self._command = custom_command.split()
        else:
            self._command = self.__default_command()

    def __default_command(self):
        for command, options in commands.items():
            path = shutil.which(command)
            if path:
                return [path] + options

    def copy(self, value):
        'Copy a cell to the system clipboard.'
        if not self._command:
            error('options.clipboard_copy_cmd not set')

        with tempfile.NamedTemporaryFile() as temp:
            with open(temp.name, 'w', encoding=options.encoding) as fp:
                fp.write(str(value))

            p = subprocess.Popen(
                self._command,
                stdin=open(temp.name, 'r', encoding=options.encoding))
            p.communicate()

    def save(self, vs, filetype):
        'Copy rows to the system clipboard.'
        if not self._command:
            error('options.clipboard_copy_cmd not set')

        with tempfile.NamedTemporaryFile() as temp:
            tempfn = temp.name + "." + filetype
            saveSheets(tempfn, vs)
            sync(1)
            p = subprocess.Popen(
                self._command,
                stdin=open(tempfn, 'r', encoding=options.encoding),
                close_fds=True)
            p.communicate()


clipboard = None


def copyToClipboard(value):
    global clipboard
    clipboard = clipboard or _Clipboard(options.clipboard_copy_cmd)
    clipboard.copy(value)
    status('copied value to clipboard')


@async
def saveToClipboard(sheet, rows, filetype=None):
    global clipboard
    clipboard = clipboard or _Clipboard(options.clipboard_copy_cmd)
    filetype = filetype or options.filetype
    vs = copy(sheet)
    vs.rows = rows
    status('copying rows to clipboard')
    clipboard.save(vs, filetype)
    status('done')
