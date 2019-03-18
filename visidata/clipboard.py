from copy import copy
import shutil
import subprocess
import sys
import tempfile
import functools

from visidata import vd, asyncthread, status, fail, option, options
from visidata import Sheet, saveSheets, Path, Column
from visidata import undoEditCell, undoEditCells, undoSheetRows

vd.cliprows = []  # list of (source_sheet, source_row_idx, source_row)
vd.clipcells = []  # list of strings

def setslice(L, a, b, M):
    L[a:b] = M

Sheet.addCommand('y', 'copy-row', 'vd.cliprows = [(sheet, cursorRowIndex, cursorRow)]')
Sheet.addCommand('d', 'delete-row', 'vd.cliprows = [(sheet, cursorRowIndex, rows.pop(cursorRowIndex))]', undo='lambda s=sheet,r=cursorRow,ridx=cursorRowIndex: s.rows.insert(ridx, r)')
Sheet.addCommand('p', 'paste-after', 'rows[cursorRowIndex+1:cursorRowIndex+1] = list(deepcopy(r) for s,i,r in vd.cliprows)', undo='lambda s=sheet,ridx=cursorRowIndex: s.rows.pop(ridx+1)')
Sheet.addCommand('P', 'paste-before', 'rows[cursorRowIndex:cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)', undo='lambda s=sheet,ridx=cursorRowIndex: s.rows.pop(ridx)')

Sheet.addCommand('gd', 'delete-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); deleteSelected()', undo=undoSheetRows)
Sheet.addCommand('gy', 'copy-selected', 'vd.cliprows = list((None, i, r) for i, r in enumerate(selectedRows)); status("%d %s to clipboard" % (len(vd.cliprows), rowtype))')

Sheet.addCommand('zy', 'copy-cell', 'vd.clipcells = [cursorDisplay]')
Sheet.addCommand('zp', 'paste-cell', 'cursorCol.setValuesTyped([cursorRow], vd.clipcells[0])', undo=undoEditCell)
Sheet.addCommand('zd', 'delete-cell', 'vd.clipcells = [cursorDisplay]; cursorCol.setValues([cursorRow], None)', undo=undoEditCell)
Sheet.addCommand('gzd', 'delete-cells', 'vd.clipcells = list(vd.sheet.cursorCol.getDisplayValue(r) for r in selectedRows); cursorCol.setValues(selectedRows, None)', undo=undoEditCells)

Sheet.addCommand('gzy', 'copy-cells', 'vd.clipcells = [vd.sheet.cursorCol.getDisplayValue(r) for r in selectedRows]; status("%d values to clipboard" % len(vd.clipcells))')
Sheet.addCommand('gzp', 'paste-cells', 'for r, v in zip(selectedRows or rows, itertools.cycle(vd.clipcells)): cursorCol.setValuesTyped([r], v)', undo=undoEditCells)

Sheet.addCommand('Y', 'syscopy-row', 'saveToClipboard(sheet, [cursorRow], input("copy current row to system clipboard as filetype: ", value=options.save_filetype))')
Sheet.addCommand('gY', 'syscopy-selected', 'saveToClipboard(sheet, selectedRows or rows, input("copy rows to system clipboard as filetype: ", value=options.save_filetype))')
Sheet.addCommand('zY', 'syscopy-cell', 'copyToClipboard(cursorDisplay)')
Sheet.addCommand('gzY', 'syscopy-cells', 'copyToClipboard("\\n".join(vd.sheet.cursorCol.getDisplayValue(r) for r in selectedRows))')

Sheet.bindkey('BUTTON2_PRESSED', 'go-mouse')
Sheet.addCommand('BUTTON2_RELEASED', 'syspaste-cells',
        'pasteFromClipboard(visibleCols[cursorVisibleColIndex:], rows[cursorRowIndex:])')
Sheet.bindkey('BUTTON2_CLICKED', 'go-mouse')

Sheet.bindkey('KEY_DC', 'delete-cell'),
Sheet.bindkey('gKEY_DC', 'delete-cells'),


option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard')
option('clipboard_paste_cmd', '', 'command to get contents of system clipboard')

# mapping of OS to list of possible (command name, command args) for copy and
# paste commands
__copy_commands = {
    # TODO TEST WINDOWS AND MAC
    'win32': [('clip', '')],
    'darwin': [('pbcopy', 'w')],
    # try these for all other platforms
    None: [('xclip', '-selection clipboard -filter'),
           ('xsel', '--clipboard --input')]
}
__paste_commands = {
    # TODO TEST WINDOWS AND MAC
    'win32': [('clip', '')],
    'darwin': [('pbpaste', '')],
    # try these for all other platforms
    None: [('xclip', '-selection clipboard -o'),
           ('xsel', '--clipboard')]
}

def detect_command(cmdlist):
    '''Detect available clipboard util and return cmdline to copy data to the system clipboard.
    cmddict is list of (platform, progname, argstr).'''

    for cmd, args in cmdlist.get(sys.platform, cmdlist[None]):
        path = shutil.which(cmd)
        if path: # see if command exists on system
            return ' '.join([path, args])
    return ''

detect_copy_command = lambda: detect_command(__copy_commands)
detect_paste_command = lambda: detect_command(__paste_commands)


@functools.lru_cache()
def clipboard():
    'Detect cmd and set option at first use, to allow option to be changed by user later.'
    if not options.clipboard_copy_cmd:
        options.clipboard_copy_cmd = detect_copy_command()
    if not options.clipboard_paste_cmd:
        options.clipboard_paste_cmd = detect_paste_command()
    return _Clipboard()


class _Clipboard:
    'Cross-platform helper to copy a cell or multiple rows to the system clipboard.'

    def get_command(self, name):
        if name not in {'copy', 'paste'}:
            raise ValueError()
        name = 'clipboard_{}_cmd'.format(name)
        cmd = getattr(options, name) or fail('options.{} not set'.format(name))
        return cmd.split()

    def paste(self):
        return subprocess.check_output(self.get_command('paste')).decode('utf-8')

    def copy(self, value):
        'Copy a cell to the system clipboard.'

        with tempfile.NamedTemporaryFile() as temp:
            with open(temp.name, 'w', encoding=options.encoding) as fp:
                fp.write(str(value))

            p = subprocess.Popen(
                self.get_command('copy'),
                stdin=open(temp.name, 'r', encoding=options.encoding),
                stdout=subprocess.DEVNULL)
            p.communicate()

    def save(self, vs, filetype):
        'Copy rows to the system clipboard.'

        # use NTF to generate filename and delete file on context exit
        with tempfile.NamedTemporaryFile(suffix='.'+filetype) as temp:
            saveSheets(Path(temp.name), vs).join()
            p = subprocess.Popen(
                self.get_command('copy'),
                stdin=open(temp.name, 'r', encoding=options.encoding),
                stdout=subprocess.DEVNULL,
                close_fds=True)
            p.communicate()

def pasteFromClipboard(cols, rows):
    text = clipboard().paste()
    for line, r in zip(text.split('\n'), rows):
        for v, c in zip(line.split('\t'), cols):
            c.setValue(r, v)

def copyToClipboard(value):
    'copy single value to system clipboard'
    clipboard().copy(value)
    status('copied value to clipboard')


@asyncthread
def saveToClipboard(sheet, rows, filetype=None):
    'copy rows from sheet to system clipboard'
    filetype = filetype or options.save_filetype
    vs = copy(sheet)
    vs.rows = rows
    status('copying rows to clipboard')
    clipboard().save(vs, filetype)
