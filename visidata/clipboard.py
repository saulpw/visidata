from copy import copy, deepcopy
import shutil
import subprocess
import sys
import tempfile
import functools

from visidata import VisiData, vd, asyncthread, option, options
from visidata import Sheet, saveSheets, Path, Column

option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard', sheettype=None)
option('clipboard_paste_cmd', '', 'command to get contents of system clipboard', sheettype=None)

VisiData.init('cliprows', list) # list of (source_sheet, source_row_idx, source_row)
VisiData.init('clipcells', list) # list of strings


def setslice(L, a, b, M):
    L[a:b] = M


@Sheet.api
def copyRows(sheet, rows):
    vd.cliprows = list((sheet, i, r) for i, r in enumerate(rows))
    if not rows:
        vd.warning('no %s selected; clipboard emptied' % sheet.rowtype)
    else:
        vd.status('copied %d %s to clipboard' % (len(rows), sheet.rowtype))

@Sheet.api
def copyCells(sheet, col, rows):
    vd.clipcells = [col.getDisplayValue(r) for r in rows]
    if not rows:
        vd.warning('no %s selected; clipboard emptied' % sheet.rowtype)
        return
    vd.status('copied %d %s.%s to clipboard' % (len(rows), sheet.rowtype, col.name))

@Sheet.api
def syscopyRows(sheet, rows):
    if not rows:
        vd.fail('no %s selected' % sheet.rowtype)
    filetype = vd.input("copy %d %s to system clipboard as filetype: " % (len(rows), sheet.rowtype), value=options.save_filetype)
    saveToClipboard(sheet, rows, filetype)
    vd.status('copied %d %s to system clipboard' % (len(rows), sheet.rowtype))

@Sheet.api
def syscopyCells(sheet, col, rows):
    if not rows:
        vd.fail('no %s selected' % sheet.rowtype)
    clipboard().copy("\n".join(col.getDisplayValue(r) for r in rows))
    vd.status('copied %s from %d %s to system clipboard' % (col.name, len(rows), sheet.rowtype))

@Sheet.api
def delete_row(sheet, rowidx):
    if not sheet.defer:
        oldrow = sheet.rows.pop(rowidx)
        vd.addUndo(sheet.rows.insert, rowidx, oldrow)
    else:
        oldrow = sheet.rows[rowidx]
        sheet.rowDeleted(oldrow)

    vd.cliprows = [(sheet, rowidx, oldrow)]

@Sheet.api
def paste_after(sheet, rowidx):
    vd.addUndo(sheet.rows.pop, rowidx+1)
    sheet.rows[rowidx+1:rowidx+1] = list(deepcopy(r) for s,i,r in vd.cliprows)

@Sheet.api
def paste_before(sheet, rowidx):
    sheet.rows[sheet.cursorRowIndex:sheet.cursorRowIndex] = list(deepcopy(r) for s,i,r in vd.cliprows)
    vd.addUndo(sheet.rows.pop, rowidx)


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
        cmd = getattr(options, name) or vd.fail('options.{} not set'.format(name))
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
            vd.sync(saveSheets(Path(temp.name), vs))
            p = subprocess.Popen(
                self.get_command('copy'),
                stdin=open(temp.name, 'r', encoding=options.encoding),
                stdout=subprocess.DEVNULL,
                close_fds=True)
            p.communicate()


@VisiData.api
def pasteFromClipboard(vd, cols, rows):
    text = vd.getLastArgs() or clipboard().paste().strip() or vd.error('system clipboard is empty')

    vd.addUndoSetValues(cols, rows)

    for line, r in zip(text.split('\n'), rows):
        for v, c in zip(line.split('\t'), cols):
            c.setValue(r, v)


@asyncthread
def saveToClipboard(sheet, rows, filetype=None):
    'copy rows from sheet to system clipboard'
    filetype = filetype or options.save_filetype
    vs = copy(sheet)
    vs.rows = rows
    vd.status('copying rows to clipboard')
    clipboard().save(vs, filetype)


Sheet.addCommand('y', 'copy-row', 'copyRows([cursorRow])', 'yank (copy) current row to clipboard')
Sheet.addCommand('d', 'delete-row', 'delete_row(cursorRowIndex)', 'delete (cut) current row and move it to clipboard')
Sheet.addCommand('p', 'paste-after', 'paste_after(cursorRowIndex)', 'paste clipboard rows after current row')
Sheet.addCommand('P', 'paste-before', 'paste_before(cursorRowIndex)', 'paste clipboard rows before current row')

Sheet.addCommand('gd', 'delete-selected', 'copyRows(selectedRows); deleteSelected()', 'delete (cut) selected rows and move them to clipboard')
Sheet.addCommand('gy', 'copy-selected', 'copyRows(selectedRows)', 'yank (copy) selected rows to clipboard')

Sheet.addCommand('zy', 'copy-cell', 'copyCells(cursorCol, [cursorRow])', 'yank (copy) current cell to clipboard')
Sheet.addCommand('zp', 'paste-cell', 'cursorCol.setValuesTyped([cursorRow], vd.clipcells[0]) if vd.clipcells else warning("no cells to paste")', 'set contents of current cell to last clipboard value')
Sheet.addCommand('zd', 'delete-cell', 'vd.clipcells = [cursorDisplay]; cursorCol.setValues([cursorRow], None)', 'delete (cut) current cell and move it to clipboard')
Sheet.addCommand('gzd', 'delete-cells', 'vd.clipcells = list(vd.sheet.cursorCol.getDisplayValue(r) for r in selectedRows); cursorCol.setValues(selectedRows, None)', 'delete (cut) contents of current column for selected rows and move them to clipboard')

Sheet.bindkey('BUTTON2_PRESSED', 'go-mouse')
Sheet.addCommand('BUTTON2_RELEASED', 'syspaste-cells', 'pasteFromClipboard(visibleCols[cursorVisibleColIndex:], rows[cursorRowIndex:])', 'paste into VisiData from system clipboard')
Sheet.bindkey('BUTTON2_CLICKED', 'go-mouse')

Sheet.addCommand('gzy', 'copy-cells', 'copyCells(cursorCol, selectedRows)', 'yank (copy) contents of current column for selected rows to clipboard')
Sheet.addCommand('gzp', 'setcol-clipboard', 'for r, v in zip(selectedRows, itertools.cycle(vd.clipcells)): cursorCol.setValuesTyped([r], v)', 'set cells of current column for selected rows to last clipboard value')

Sheet.addCommand('Y', 'syscopy-row', 'syscopyRows([cursorRow])', 'yank (copy) current row to system clipboard (using options.clipboard_copy_cmd)')

Sheet.addCommand('gY', 'syscopy-selected', 'syscopyRows(selectedRows)', 'yank (copy) selected rows to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('zY', 'syscopy-cell', 'syscopyCells(cursorCol, [cursorRow])', 'yank (copy) current cell to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('gzY', 'syscopy-cells', 'syscopyCells(cursorCol, selectedRows)', 'yank (copy) contents of current column from selected rows to system clipboard (using options.clipboard_copy_cmd')

Sheet.bindkey('KEY_DC', 'delete-cell'),
Sheet.bindkey('gKEY_DC', 'delete-cells'),
