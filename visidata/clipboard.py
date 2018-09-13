from copy import copy
import shutil
import subprocess
import sys
import tempfile
import functools

from visidata import vd, asyncthread, sync, status, fail, option, options
from visidata import Sheet, saveSheets

vd.cliprows = []  # list of (source_sheet, source_row_idx, source_row)
vd.clipcells = []  # list of strings

Sheet.addCommand('y', 'copy-row', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]')
Sheet.addCommand('d', 'delete-row', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]')
Sheet.addCommand('p', 'paste-after', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)')
Sheet.addCommand('P', 'paste-before', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)')

Sheet.addCommand('gd', 'delete-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()')
Sheet.addCommand('gy', 'copy-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); status("%d %s to clipboard" % (len(vd.cliprows), rowtype))')

Sheet.addCommand('zy', 'copy-cell', 'vd.clipcells = [cursorDisplay]')
Sheet.addCommand('zp', 'paste-cell', 'cursorCol.setValuesTyped([cursorRow], vd.clipcells[0])')
Sheet.addCommand('zd', 'delete-cell', 'vd.clipcells = [cursorDisplay]; cursorCol.setValues([cursorRow], None)')
Sheet.addCommand('gzd', 'delete-cells', 'vd.clipcells = list(sheet.cursorCol.getDisplayValue(r) for r in selectedRows); cursorCol.setValues(selectedRows, None)')

Sheet.addCommand('gzy', 'copy-cells', 'vd.clipcells = [sheet.cursorCol.getDisplayValue(r) for r in selectedRows]; status("%d values to clipboard" % len(vd.clipcells))')
Sheet.addCommand('gzp', 'paste-cells', 'for r, v in zip(selectedRows or rows, itertools.cycle(vd.clipcells)): cursorCol.setValuesTyped([r], v)')

Sheet.addCommand('Y', 'syscopy-row', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.filetype or "csv"))')
Sheet.addCommand('gY', 'syscopy-selected', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.filetype or "csv"))')
Sheet.addCommand('zY', 'syscopy-cell', 'copyToClipboard(cursorDisplay)')
Sheet.addCommand('gzY', 'syscopy-cells', 'copyToClipboard("\n".join(sheet.cursorCol.getDisplayValue(r) for r in selectedRows))')

Sheet.bindkey('KEY_DC', 'delete-cell'),
Sheet.bindkey('gKEY_DC', 'delete-cells'),


option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard')

__clipboard_commands = [
    ('win32',  'clip', ''),                                      # Windows Vista+
    ('darwin', 'pbcopy', 'w'),                                   # macOS
    (None,     'xclip', '-selection clipboard -filter'),         # Linux etc.
    (None,     'xsel', '--clipboard --input'),                   # Linux etc.
]

def detect_command(cmdlist):
    '''Detect available clipboard util and return cmdline to copy data to the system clipboard.
    cmddict is list of (platform, progname, argstr).'''

    for platform, command, args in cmdlist:
        if platform is None or sys.platform == platform:
            path = shutil.which(command)
            if path:
                return ' '.join([path, args])

    return ''

detect_clipboard_command = lambda: detect_command(__clipboard_commands)

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
        cmd = options.clipboard_copy_cmd or fail('options.clipboard_copy_cmd not set')
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
