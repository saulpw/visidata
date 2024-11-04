from copy import copy, deepcopy
import shutil
import subprocess
import io
import sys
import tempfile
import functools
import os
import itertools

from visidata import VisiData, vd, asyncthread, SettableColumn
from visidata import Sheet, Path, Column

if sys.platform == 'win32':
    syscopy_cmd_default = 'clip.exe'
    syspaste_cmd_default = 'powershell -command Get-Clipboard'
elif sys.platform == 'darwin':
    syscopy_cmd_default = 'pbcopy w'
    syspaste_cmd_default = 'pbpaste'
else:
    if 'WAYLAND_DISPLAY' in os.environ:
        syscopy_cmd_default = 'wl-copy'
        syspaste_cmd_default = 'wl-paste'
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
        encoding='utf-8',
        stdout=subprocess.DEVNULL)

    vd.status('copied value to system clipboard')

@Sheet.api
def setColClipboard(sheet):
    if not vd.memory.clipcells:
        vd.warning("nothing to paste from clipcells")
        return
    sheet.cursorCol.setValuesTyped(sheet.onlySelectedRows, *vd.memory.clipcells)

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
        with tempfile.NamedTemporaryFile() as temp:
            temp.close()  #2118

            vd.sync(vd.saveSheets(Path(f'{temp.name}.{filetype}', fptext=buf), vs, confirm_overwrite=False))
            subprocess.run(
                sheet.options.clipboard_copy_cmd.split(),
                input=buf.getvalue(),
                encoding='utf-8',
                stdout=subprocess.DEVNULL)


@VisiData.api
def sysclipValue(vd):
    cmd = vd.options.clipboard_paste_cmd
    return subprocess.check_output(vd.options.clipboard_paste_cmd.split()).decode('utf-8')


@VisiData.api
@asyncthread
def pasteFromClipboard(vd, cols, rows):
    text = vd.getLastArgs() or vd.sysclipValue().strip() or vd.fail('nothing to paste from system clipboard')

    vd.addUndoSetValues(cols, rows)
    lines = text.split('\n')
    if not lines:
        vd.warning('nothing to paste from system clipboard')
        return

    vs = cols[0].sheet
    newrows = [vs.newRow() for i in range(len(lines)-len(rows))]
    if newrows:
        rows.extend(newrows)
        vs.addRows(newrows)

    for line, r in zip(lines, rows):
        for v, c in zip(line.split('\t'), cols):
            c.setValue(r, v)


@Sheet.api
def delete_row(sheet, rowidx):
    if not sheet.rows:
        vd.fail("no row to delete")
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
@asyncthread
def paste_after(sheet, rowidx):
    'Paste rows from *vd.cliprows* at *rowidx*.'
    if not vd.memory.cliprows:  #1793
        vd.warning('nothing to paste from cliprows')
        return

    for col in vd.memory.clipcols[sheet.nVisibleCols:]:
        newcol = SettableColumn()
        newcol.__setstate__(col.__getstate__())
        sheet.addColumn(newcol)

    addedRows = []

    for extrow in vd.memory.cliprows:
        if isinstance(extrow, Column):
            newrow = copy(extrow)
        else:
            newrow = sheet.newRow()
            for col, extcol in zip(sheet.visibleCols, vd.memory.clipcols):
                col.setValue(newrow, extcol.getTypedValue(extrow))

        addedRows.append(newrow)

    sheet.addRows(addedRows, index=rowidx)


Sheet.addCommand('y', 'copy-row', 'copyRows([cursorRow])', 'yank (copy) current row to clipboard')

Sheet.addCommand('p', 'paste-after', 'paste_after(cursorRowIndex)', 'paste clipboard rows after current row')
Sheet.addCommand('P', 'paste-before', 'paste_after(cursorRowIndex-1)', 'paste clipboard rows before current row')

Sheet.addCommand('gy', 'copy-selected', 'copyRows(onlySelectedRows)', 'yank (copy) selected rows to clipboard')

Sheet.addCommand('zy', 'copy-cell', 'copyCells(cursorCol, [cursorRow]); vd.memoValue("clipval", cursorTypedValue, cursorDisplay)', 'yank (copy) current cell to clipboard')
Sheet.addCommand('zp', 'paste-cell', 'cursorCol.setValuesTyped([cursorRow], vd.memory.clipval) if vd.memory.clipval else vd.warning("nothing to paste from clipval")', 'set contents of current cell to last clipboard value')

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
Sheet.addCommand('gzp', 'setcol-clipboard', 'setColClipboard()', 'set cells of current column for selected rows to last clipboard value')

Sheet.addCommand('Y', 'syscopy-row', 'syscopyCells(visibleCols, [cursorRow])', 'yank (copy) current row to system clipboard (using options.clipboard_copy_cmd)')

Sheet.addCommand('gY', 'syscopy-selected', 'syscopyCells(visibleCols, onlySelectedRows)', 'yank (copy) selected rows to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('zY', 'syscopy-cell', 'syscopyValue(cursorDisplay)', 'yank (copy) current cell to system clipboard (using options.clipboard_copy_cmd)')
Sheet.addCommand('gzY', 'syscopy-cells', 'syscopyCells([cursorCol], onlySelectedRows, filetype="txt")', 'yank (copy) contents of current column from selected rows to system clipboard (using options.clipboard_copy_cmd')

Sheet.addCommand('x', 'cut-row', 'copyRows([sheet.delete_row(cursorRowIndex)]); defer and cursorDown(1)', 'delete (cut) current row and move it to clipboard')
Sheet.addCommand('gx', 'cut-selected', 'copyRows(onlySelectedRows); deleteSelected()', 'delete (cut) selected rows and move them to clipboard')
Sheet.addCommand('zx', 'cut-cell', 'copyCells(cursorCol, [cursorRow]); cursorCol.setValues([cursorRow], None)', 'delete (cut) current cell and move it to clipboard')
Sheet.addCommand('gzx', 'cut-cells', 'copyCells(cursorCol, onlySelectedRows); cursorCol.setValues(onlySelectedRows, None)', 'delete (cut) contents of current column for selected rows and move them to clipboard')


Sheet.bindkey('Del', 'delete-cell'),
Sheet.bindkey('gDel', 'delete-cells'),

vd.addMenuItems('''
    Edit > Delete > current row > delete-row
    Edit > Delete > current cell > delete-cell
    Edit > Delete > selected rows > delete-selected
    Edit > Delete > selected cells > delete-cells
    Edit > Copy > current cell > copy-cell
    Edit > Copy > current row > copy-row
    Edit > Copy > selected cells > copy-cells
    Edit > Copy > selected rows > copy-selected
    Edit > Copy > to system clipboard > current cell > syscopy-cell
    Edit > Copy > to system clipboard > current row > syscopy-row
    Edit > Copy > to system clipboard > selected cells > syscopy-cells
    Edit > Copy > to system clipboard > selected rows > syscopy-selected
    Edit > Cut > current row > cut-row
    Edit > Cut > selected cells > cut-selected
    Edit > Cut > current cell > cut-cell
    Edit > Paste > row after > paste-after
    Edit > Paste > row before > paste-before
    Edit > Paste > into selected cells > setcol-clipboard
    Edit > Paste > into current cell > paste-cell
    Edit > Paste > from system clipboard > cells at cursor > syspaste-cells
    Edit > Paste > from system clipboard > selected cells > syspaste-cells-selected
''')
