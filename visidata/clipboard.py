from copy import copy, deepcopy
import shutil
import subprocess
import io
import sys
import tempfile
import functools

from visidata import VisiData, vd, asyncthread
from visidata import Sheet, Path

if sys.platform == 'win32':
    syscopy_cmd_default = 'clip'
    syspaste_cmd_default = 'clip'
elif sys.platform == 'darwin':
    syscopy_cmd_default = 'pbcopy w'
    syspaste_cmd_default = 'pbpaste'
else:
    syscopy_cmd_default = 'xclip -selection clipboard -filter'  # xsel --clipboard --input
    syspaste_cmd_default = 'xclip -selection clipboard -o'  # xsel --clipboard

vd.option('clipboard_copy_cmd', syscopy_cmd_default, 'command to copy stdin to system clipboard', sheettype=None)
vd.option('clipboard_paste_cmd', syspaste_cmd_default, 'command to send contents of system clipboard to stdout', sheettype=None)


@Sheet.api
def copyRows(sheet, rows):
    vd.memory.cliprows = rows
    vd.memory.clipcols = list(sheet.visibleCols)
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


@Sheet.api
def syscopyValue(sheet, val):
    # pipe val to stdin of clipboard command

    p = subprocess.run(
        sheet.options.clipboard_copy_cmd.split(),
        input=val,
        encoding=sheet.options.encoding,
        stdout=subprocess.DEVNULL)

    vd.status('copied value to system clipboard')


@Sheet.api
def syscopyCells(sheet, cols, rows, filetype=None):
    filetype = filetype or vd.input("copy %d %s as filetype: " % (len(rows), sheet.rowtype), value=sheet.options.save_filetype or 'tsv')
    sheet.syscopyCells_async(cols, rows, filetype)


@Sheet.api
@asyncthread
def syscopyCells_async(sheet, cols, rows, filetype):
    vs = copy(sheet)
    vs.rows = rows or vd.fail('no %s selected' % sheet.rowtype)
    vs.columns = cols

    vd.status(f'copying {vs.nRows} {vs.rowtype} to system clipboard as {filetype}')

    with io.StringIO() as buf:
        vd.sync(vd.saveSheets(Path(sheet.name+'.'+filetype, fptext=buf), vs))
        subprocess.run(
            sheet.options.clipboard_copy_cmd.split(),
            input=buf.getvalue(),
            encoding=sheet.options.encoding,
            stdout=subprocess.DEVNULL)


@VisiData.api
def sysclip_value(vd):
    cmd = vd.options.clipboard_paste_cmd
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
        # clear the deleted row from selected rows
        if sheet.isSelected(oldrow):
            sheet.addUndoSelection()
            sheet.unselectRow(oldrow)
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
