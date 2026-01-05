from visidata import vd, BaseSheet, VisiData, asyncthread, Progress


@VisiData.property
def prevCmdlogRow(vd):
    if not vd.cmdlog.rows:
        vd.fail("no recent command to repeat")

    return vd.cmdlog.rows[-1]


@BaseSheet.api
def repeat_last(sheet, cmdrow):
    vd.queueCommand(cmdrow.longname, cmdrow.input, sheet=sheet)


@BaseSheet.api
@asyncthread
def repeat_for_n(sheet, cmdrow, n=1):
    for i in range(n):
        vd.queueCommand(cmdrow.longname, cmdrow.input, sheet=sheet)


@BaseSheet.api
@asyncthread
def repeat_for_selected(sheet, cmdrow):
    for idx, r in enumerate(Progress(vd.sheet.rows)):
        if vd.sheet.isSelected(r):
            vd.queueCommand(cmdrow.longname, cmdrow.input, row=idx, sheet=sheet)


BaseSheet.addCommand('', 'repeat-last', 'repeat_last(vd.prevCmdlogRow)', 'run most recent command with an empty, queried input')
BaseSheet.addCommand('', 'repeat-input', 'repeat_for_n(vd.prevCmdlogRow, 1)', 'run previous modifying command (incl input)')
BaseSheet.addCommand('', 'repeat-input-n', 'repeat_for_n(vd.prevCmdlogRow, input("# times to repeat prev command:", value=1))', 'run previous command (incl its input) N times')
BaseSheet.addCommand('', 'repeat-input-selected', 'repeat_for_selected(vd.prevCmdlogRow)', 'run previous command (incl its input) for each selected row')

vd.addMenuItem('Edit', 'Repeat', 'last command', 'repeat-input')
vd.addMenuItem('Edit', 'Repeat', 'last command N times', 'repeat-input-n')
vd.addMenuItem('Edit', 'Repeat', 'last command for all selected rows', 'repeat-input-selected')
