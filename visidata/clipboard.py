import shutil
import subprocess
import sys
import tempfile

from visidata import *

# adds vd.clipvalue and vd.cliprows
# vd.cliprows = [(source_sheet, source_row_idx, source_row)]

globalCommand('y', 'copy-row', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]')
globalCommand('d', 'delete-row', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]')
globalCommand('p', 'paste-after', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)')
globalCommand('P', 'paste-before', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)')

globalCommand('gd', 'delete-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()')
globalCommand('gy', 'copy-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); status("%d %s to clipboard" % (len(vd.cliprows), rowtype))')

globalCommand('zy', 'copy-cell', 'vd.clipvalue = cursorDisplay')
globalCommand('gzp', 'paste-selected', 'cursorCol.setValues(selectedRows or rows, vd.clipvalue)')
globalCommand('zp', 'paste-cell', 'cursorCol.setValue(cursorRow, vd.clipvalue)')

globalCommand('Y', 'syscopy-row', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.filetype or "csv"))')
globalCommand('gY', 'syscopy-selected', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.filetype or "csv"))')
globalCommand('zY', 'syscopy-cell', 'copyToClipboard(cursorDisplay)')

option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard')

__clipboard_commands = {
    ('clip', 'win32'):    '',                                      # Windows Vista+
    ('pbcopy', 'darwin'): 'w',                                     # macOS
    ('xclip', None):      '-selection clipboard -filter',          # Linux etc.
    ('xsel', None):       '--clipboard --input',                   # Linux etc.
}

def detect_clipboard_command():
    'Detect available clipboard util and return cmdline to copy data to the system clipboard.'
    for (command, platform), options in __clipboard_commands.items():
        if platform is None or sys.platform == platform:
            path = shutil.which(command)
            if path:
                return ' '.join([path, options])

    return ''

@functools.lru_cache()
def clipboard():
    'Detect cmd and set option at first use, to allow option to be changed by user later.'
    if not options.clipboard_copy_cmd:
        options.clipboard_copy_cmd = detect_clipboard_command()
    return _Clipboard()


class _Clipboard:
    'Cross-platform helper to copy a cell or multiple rows to the system clipboard.'

    @property
    def command(self):
        'Return cmdline cmd+args (as list for Popen) to copy data to the system clipboard.'
        cmd = options.clipboard_copy_cmd
        if not cmd:
            error('options.clipboard_copy_cmd not set')
        return cmd.split()

    def copy(self, value):
        'Copy a cell to the system clipboard.'

        with tempfile.NamedTemporaryFile() as temp:
            with open(temp.name, 'w', encoding=options.encoding) as fp:
                fp.write(str(value))

            p = subprocess.Popen(
                self.command,
                stdin=open(temp.name, 'r', encoding=options.encoding),
                stdout=subprocess.DEVNULL)
            p.communicate()

    def save(self, vs, filetype):
        'Copy rows to the system clipboard.'

        # use NTF to generate filename and delete file on context exit
        with tempfile.NamedTemporaryFile(suffix='.'+filetype) as temp:
            saveSheets(temp.name, vs)
            sync(1)
            p = subprocess.Popen(
                self.command,
                stdin=open(temp.name, 'r', encoding=options.encoding),
                stdout=subprocess.DEVNULL,
                close_fds=True)
            p.communicate()


def copyToClipboard(value):
    'copy single value to system clipboard'
    clipboard().copy(value)
    status('copied value to clipboard')


@asyncthread
def saveToClipboard(sheet, rows, filetype=None):
    'copy rows from sheet to system clipboard'
    filetype = filetype or options.filetype
    vs = copy(sheet)
    vs.rows = rows
    status('copying rows to clipboard')
    clipboard().save(vs, filetype)
