from copy import copy, deepcopy
import shutil
import subprocess
import sys
import tempfile
import functools

from visidata import VisiData, vd, asyncthread
from visidata import Sheet, Path

vd.option('clipboard_copy_cmd', '', 'command to copy stdin to system clipboard', sheettype=None)
vd.option('clipboard_paste_cmd', '', 'command to get contents of system clipboard', sheettype=None)


@Sheet.api
def copyRows(sheet, rows):
    vd.memory.cliprows = rows
    if not rows:
        vd.warning('no %s selected; clipboard emptied' % sheet.rowtype)
    else:
        vd.status('copied %d %s to clipboard' % (len(rows), sheet.rowtype))

@Sheet.api
def copyCells(sheet, col, rows):
    vd.memory.clipcells = [col.getTypedValue(r) for r in rows]
    if not rows:
        vd.warning('no %s selected; clipboard emptied' % sheet.rowtype)
        return
    vd.status('copied %d %s.%s to clipboard' % (len(rows), sheet.rowtype, col.name))


def _detect_command(cmdlist):
    '''Detect available clipboard util and return cmdline to copy data to the system clipboard.
    cmddict is list of (platform, progname, argstr).'''

    for cmd, args in cmdlist.get(sys.platform, cmdlist[None]):
        path = shutil.which(cmd)
        if path: # see if command exists on system
            return ' '.join([path, args])
    return ''


def detect_syscopy_cmd(sheet):
    cmd = sheet.options.clipboard_copy_cmd
    if not cmd:
        __copy_commands = {
            'win32': [('clip', '')],
            'darwin': [('pbcopy', 'w')],
            None: [('xclip', '-selection clipboard -filter'),
                ('xsel', '--clipboard --input')]
        }
        cmd = sheet.options.clipboard_copy_cmd = _detect_command(__copy_commands)
    return cmd


def detect_syspaste_cmd():
    cmd = vd.options.clipboard_paste_cmd
    if not cmd:
        __paste_commands = {
            'win32': [('clip', '')],
            'darwin': [('pbpaste', '')],
                None: [('xclip', '-selection clipboard -o'),
                    ('xsel', '--clipboard')]
        }
        cmd = vd.options.clipboard_paste_cmd = _detect_command(__paste_commands)
    return cmd


@Sheet.api
def syscopyValue(sheet, val):
    # use NTF to generate filename and delete file on context exit
    with tempfile.NamedTemporaryFile(suffix='.txt') as temp:
        with open(temp.name, "w", encoding=sheet.options.encoding) as fp:
            fp.write(val)

        p = subprocess.Popen(
            detect_syscopy_cmd(sheet).split(),
            stdin=open(temp.name, 'r', encoding=sheet.options.encoding),
            stdout=subprocess.DEVNULL,
            close_fds=True)
        p.communicate()

    vd.status('copied value to system clipboard')


@Sheet.api
def syscopyCells(sheet, cols, rows, filetype=None):
    filetype = filetype or vd.input("copy %d %s as filetype: " % (len(rows), sheet.rowtype), value=sheet.options.save_filetype)
    sheet.syscopyCells_async(cols, rows, filetype)


@Sheet.api
@asyncthread
def syscopyCells_async(sheet, cols, rows, filetype):
    vs = copy(sheet)
    vs.rows = rows or vd.fail('no %s selected' % sheet.rowtype)
    vs.columns = cols

    cmd = detect_syscopy_cmd(sheet)
    vd.status(f'copying {vs.nRows} {vs.rowtype} to system clipboard as {filetype}')

    # use NTF to generate filename and delete file on context exit
    with tempfile.NamedTemporaryFile(suffix='.'+filetype) as temp:
        vd.sync(vd.saveSheets(Path(temp.name), vs))
        p = subprocess.Popen(
            sheet.options.clipboard_copy_cmd.split(),
            stdin=open(temp.name, 'r', encoding=sheet.options.encoding),
            stdout=subprocess.DEVNULL,
            close_fds=True)
        p.communicate()


@VisiData.api
def sysclip_value(vd):
    cmd = detect_syspaste_cmd()
    return subprocess.check_output(vd.options.clipboard_paste_cmd.split()).decode('utf-8')


@VisiData.api
@asyncthread
def pasteFromClipboard(vd, cols, rows):
    text = vd.getLastArgs() or vd.sysclip_value().strip() or vd.fail('system clipboard is empty')

    vd.addUndoSetValues(cols, rows)

    for line, r in zip(text.split('\n'), rows):
        for v, c in zip(line.split('\t'), cols):
            c.setValue(r, v)


@Sheet.api
def delete_row(sheet, rowidx):
    if not sheet.defer:
        oldrow = sheet.rows.pop(rowidx)
        vd.addUndo(sheet.rows.insert, rowidx, oldrow)
    else:
        oldrow = sheet.rows[rowidx]
        sheet.rowDeleted(oldrow)

    sheet.setModified()
    return oldrow

@Sheet.api
def paste_after(sheet, rowidx):
    to_paste = list(deepcopy(r) for r in reversed(vd.memory.cliprows))
    sheet.addRows(to_paste, index=rowidx)



Sheet.addCommand('y', 'copy-row', 'copyRows([cursorRow])', 'yank (copy) current row to clipboard')

Sheet.addCommand('p', 'paste-after', 'paste_after(cursorRowIndex)', 'paste clipboard rows after current row')
Sheet.addCommand('P', 'paste-before', 'paste_after(cursorRowIndex-1)', 'paste clipboard rows before current row')

Sheet.addCommand('gy', 'copy-selected', 'copyRows(onlySelectedRows)', 'yank (copy) selected rows to clipboard')

Sheet.addCommand('zy', 'copy-cell', 'copyCells(cursorCol, [cursorRow]); vd.memo("clipval", cursorCol, cursorRow)', 'yank (copy) current cell to clipboard')
Sheet.addCommand('zp', 'paste-cell', 'cursorCol.setValuesTyped([cursorRow], vd.memory.clipval)', 'set contents of current cell to last clipboard value')

Sheet.addCommand('d', 'delete-row', 'delete_row(cursorRowIndex); defer and cursorDown(1)', 'delete current row')
Sheet.addCommand('gd', 'delete-selected', 'deleteSelected()', 'delete selected rows')
Sheet.addCommand('zd', 'delete-cell', 'cursorCol.setValues([cursorRow], options.null_value)', 'delete current cell (set to None)')
Sheet.addCommand('gzd', 'delete-cells', 'cursorCol.setValues(onlySelectedRows, options.null_value)', 'delete contents of current column for selected rows (set to None)')

Sheet.bindkey('BUTTON2_PRESSED', 'go-mouse')
Sheet.addCommand('BUTTON2_RELEASED', 'syspaste-cells', 'pasteFromClipboard(visibleCols[cursorVisibleColIndex:], rows[cursorRowIndex:])', 'paste from system clipboard to region starting at cursor')
Sheet.bindkey('BUTTON2_CLICKED', 'go-mouse')
Sheet.bindkey('zP', 'syspaste-cells')
Sheet.addCommand('gzP', 'syspaste-cells-selected', 'pasteFromClipboard(visibleCols[cursorVisibleColIndex:], someSelectedRows)', 'paste from system clipboard to selected cells')

Sheet.addCommand('gzy', 'copy-cells', 'copyCells(cursorCol, onlySelectedRows)', 'yank (copy) contents of current column for selected rows to clipboard')
Sheet.addCommand('gzp', 'setcol-clipboard', 'for r, v in zip(onlySelectedRows, itertools.cycle(vd.memory.clipcells or [None])): cursorCol.setValuesTyped([r], v)', 'set cells of current column for selected rows to last clipboard value')

Sheet.addCommand('Y', 'syscopy-row', 'syscopyCells(visibleCols, [cursorRow])', 'yank (copy) current row to system clipboard (using options.clipboard_copy_cmd)')

Sheet.addCommand('gY', 'syscopy-selected', 'syscopyCells(visibleCols, onlySelectedRows)', 'yank (copy) selected rows to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('zY', 'syscopy-cell', 'syscopyValue(cursorDisplay)', 'yank (copy) current cell to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('gzY', 'syscopy-cells', 'syscopyCells([cursorCol], onlySelectedRows, filetype="txt")', 'yank (copy) contents of current column from selected rows to system clipboard (using options.clipboard_copy_cmd')

Sheet.addCommand('x', 'cut-row', 'copyRows([sheet.delete_row(cursorRowIndex)]); defer and cursorDown(1)', 'delete (cut) current row and move it to clipboard')
Sheet.addCommand('gx', 'cut-selected', 'copyRows(onlySelectedRows); deleteSelected()', 'delete (cut) selected rows and move them to clipboard')
Sheet.addCommand('zx', 'cut-cell', 'copyCells(cursorCol, [cursorRow]); cursorCol.setValues([cursorRow], None)', 'delete (cut) current cell and move it to clipboard')
Sheet.addCommand('gzx', 'cut-cells', 'copyCells(cursorCol, onlySelectedRows); cursorCol.setValues(onlySelectedRows, None)', 'delete (cut) contents of current column for selected rows and move them to clipboard')


Sheet.bindkey('KEY_DC', 'delete-cell'),
Sheet.bindkey('gKEY_DC', 'delete-cells'),
