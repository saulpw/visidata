from copy import copy
import os
from functools import wraps

from visidata.cmdlog import CommandLog, CommandLogJsonl
from visidata import vd, UNLOADED, asyncthread
from visidata import IndexSheet, VisiData, Sheet, Path, VisiDataMetaSheet, Column, ItemColumn, BaseSheet, GuideSheet

vd.macroMode = None
vd.macrobindings = {}

class MacroSheet(IndexSheet):
    help = '''
        # Macros Sheet
        This is a list of user-defined macros.

        - `Enter` to open the current macro.
        - `d` to mark macro for delete; `z Ctrl+S` to commit.
    '''
    columns = [
        Column('longname', getter=lambda c,vs: vs.name),
        Column('keystrokes', getter=lambda c,vs: vs.keystrokes),
        Column('num_commands', type=int, getter=lambda c,vs: len(vs)),
        Column('source', width=0, getter=lambda c,vs: vs.source),
    ]
    rowtype = 'macros'
    defer = True
    def iterload(self):
        for ks, fn in self.source.rows:
            fp = Path(fn)
            if fp.ext == 'vd':
                vs = vd.loadInternalSheet(CommandLog, fp)
            elif fp.ext == 'vdj':
                vs = vd.loadInternalSheet(CommandLogJsonl, fp)
            else:
                vd.warning(f'failed to load macro {fn}')
                continue
            vs.keystrokes = ks
            vd.setMacro(ks, vs)
            yield vs

    def commitDeleteRow(self, row):
        self.source.deleteBy(lambda r: r.filename == str(row.source), commit=True, undo=False)
        try:
            row.source.unlink()
        except Exception as e:
            vd.exceptionCaught(e)

    @asyncthread
    def putChanges(self):
        self.commitDeletes()  #1569

        vd.saveSheets(self.source.source, self.source, confirm_overwrite=False)
        self._deferredDels.clear()
        self.reload()

    def newRow(self):
        vd.fail('add macros with `m` instead')


@VisiData.lazy_property
def macrosheet(vd):
    macrospath = Path(os.path.join(vd.options.visidata_dir, 'macros.tsv'))
    macrosheet = vd.loadInternalSheet(VisiDataMetaSheet, macrospath, columns=(ItemColumn('command', 0), ItemColumn('filename', 1))) or vd.error('error loading macros')

    real_macrosheet = MacroSheet('user_macros', rows=[], source=macrosheet)
    real_macrosheet.reload()

    return real_macrosheet

@VisiData.api
def runMacro(vd, binding:str):
    vd.replay_sync(vd.macrobindings[binding])

@VisiData.api
def setMacro(vd, ks, vs):
    'Set *ks* which is either a keystroke or a longname to run the cmdlog in *vs*.'
    vd.macrobindings[ks] = vs
    if vd.isLongname(ks):
        BaseSheet.addCommand('', ks, f'runMacro("{ks}")')
    else:
        BaseSheet.addCommand(ks, vs.name, f'runMacro("{ks}")')


@CommandLogJsonl.api
def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = rows
        macropath = Path(vd.fnSuffix(str(Path(vd.options.visidata_dir)/ks)))
        vd.save_vdj(macropath, vs)
        vd.setMacro(ks, vs)
        vd.macrosheet.source.append_tsv_row((ks, macropath))
        vd.sync(vd.macrosheet.source.reload())
        vd.sync(vd.macrosheet.reload())


# needs to happen before, because the original afterExecSheet resets vd.activeCommand to None
@CommandLogJsonl.before
def afterExecSheet(cmdlog, sheet, escaped, err):
    if vd.macroMode and (vd.activeCommand is not None) and (vd.activeCommand is not UNLOADED) and (vd.isLoggableCommand(vd.activeCommand.longname)):
        cmd = copy(vd.activeCommand)
        cmd.sheet = ''
        vd.macroMode.addRow(cmd)


@CommandLogJsonl.api
def startMacro(cmdlog):
    if vd.macroMode:
        try:
            ks = vd.input('bind macro to: ', help=f'''
                # Finish recording macro
                Type in either a longname like `happy-time` (with at least one hyphen),
                   or spell out a keybinding (like `Alt+b`) manually.

                - Prefixes allowed with a keybinding: `{'  '.join(vd.allPrefixes)}`
                - Press `Ctrl+N` and then press another keystroke to spell that keystroke.
                - Press `Ctrl+C` to cancel the macro recording.
            ''')
            while ks in vd.macrobindings:
                ks = vd.input(f'{ks} already in use; set macro to keybinding: ')
            vd.cmdlog.saveMacro(vd.macroMode.rows, ks)
        finally:
            vd.macroMode = None
    else:
        vd.status("recording macro; stop recording with `m`")
        vd.macroMode = CommandLogJsonl('current_macro', rows=[])

@VisiData.before
def run(vd, *args, **kwargs):
    vd.macrosheet

class MacrosGuide(GuideSheet):
    guide = '''# Macros
Macros allow you to bind a series of commands to a key and then replay those commands within a session by using that keystroke.

The basic usage is:
    1. Press `m` (macro-record) to begin recording the macro.
    2. Go through the commands you wish to record.
    3. Then type `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

The macro will then be executed everytime the provided keystroke is used. Note: the Alt+keys and the function keys are left unbound; overridding other keys may conflict with existing bindings, now or in the future.

Executing a macro will the series of commands starting on the current row and column on the current sheet.

# The Macros Sheet

Use `gm` (`macro-sheet`) to open an index existing macros.

Macros can be marked for deletion (with `d`). Changes can then be committed with `z Ctrl+S`.

`Enter` will open the macro in the current row, and you can view the series of commands composing it.'''


Sheet.addCommand('m', 'macro-record', 'vd.cmdlog.startMacro()', 'record macro')
Sheet.addCommand('gm', 'macro-sheet', 'vd.push(vd.macrosheet)', 'open macros sheet')

vd.addMenuItems('''
    System > Macros sheet > macro-sheet
''')

vd.addGuide('MacrosSheet', MacrosGuide())
