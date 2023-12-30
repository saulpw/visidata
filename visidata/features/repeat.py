from visidata import vd, BaseSheet

BaseSheet.addCommand('', 'repeat-last', 'execCommand(vd.cmdlog.rows[-1].longname) if vd.cmdlog.rows else fail("no recent command to repeat")', 'run most recent command with an empty, queried input')
BaseSheet.addCommand('', 'repeat-input', 'r = copy(vd.cmdlog.rows[-1]) if vd.cmdlog.rows else fail("no recent command to repeat"); vd.cmdlog.repeat_for_n(r, 1)', 'run previous modifying command (incl input)')
BaseSheet.addCommand('', 'repeat-input-n', 'r = copy(vd.cmdlog.rows[-1]) if vd.cmdlog.rows else fail("no recent command to repeat"); vd.cmdlog.repeat_for_n(r, input("# times to repeat prev command:", value=1))', 'run previous command (incl its input) N times')
BaseSheet.addCommand('', 'repeat-input-selected', 'r = copy(vd.cmdlog.rows[-1]) if vd.cmdlog.rows else fail("no recent command to repeat"); vd.cmdlog.repeat_for_selected(r)', 'run previous command (incl its input) for each selected row')

vd.addMenuItem('Edit', 'Repeat', 'last command', 'repeat-input')
vd.addMenuItem('Edit', 'Repeat', 'last command N times', 'repeat-input-n')
vd.addMenuItem('Edit', 'Repeat', 'last command for all selected rows', 'repeat-input-selected')
