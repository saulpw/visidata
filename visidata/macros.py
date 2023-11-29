from copy import copy
from functools import wraps

from visidata.cmdlog import CommandLog, CommandLogJsonl
from visidata import vd, UNLOADED, asyncthread, vlen
from visidata import IndexSheet, VisiData, Sheet, Path, VisiDataMetaSheet, Column, ItemColumn, BaseSheet, GuideSheet
from visidata import IndexSheet, VisiData, Sheet, Path, VisiDataMetaSheet, Column, ItemColumn, AttrColumn, BaseSheet, GuideSheet

vd.macroMode = None
vd.macrobindings = {}


@VisiData.stored_property
def macros_list(vd):
    return []


class MacroSheet(IndexSheet):
    help = '''
        # Macros Sheet
        This is a list of user-defined macros.

        - `Enter` to open the current macro.
        - `d` to mark macro for delete; `z Ctrl+S` to commit.
    '''
    columns = [
        AttrColumn('binding', 'keystrokes'),
        Column('num_commands', type=vlen),
        AttrColumn('source', width=0),
    ]
    rowtype = 'macros'
    defer = True
    def iterload(self):
        yield from vd.macrobindings.values()

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
    return MacroSheet('user_macros', source=vd.macrobindings)

@VisiData.api
def loadMacro(vd, p:Path):
    if p.ext == 'vd':
        return vd.loadInternalSheet(CommandLog, p)
    elif p.ext == 'vdj':
        return vd.loadInternalSheet(CommandLogJsonl, p)
    else:
        vd.warning(f'failed to load macro {fn}')

@VisiData.api
def runMacro(vd, binding:str):
    vd.replay_sync(vd.macrobindings[binding])


@VisiData.api
def setMacro(vd, ks, vs):
    'Set *ks* which is either a keystroke or a longname to run the cmdlog in *vs*.'
    vs.keystrokes = ks
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
        vd.macros_list.append(dict(command=ks, filename=macropath))
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
@asyncthread
def run(vd, *args, **kwargs):
    for r in vd.macros_list:
        ks = r['command']
        fn = r['filename']
        p = Path(fn)
        vd.setMacro(ks, vd.loadMacro(p))


class MacrosGuide(GuideSheet):
    guide = '''# Macros
Macros allow you to bind a command sequence to a keystroke or longname, to replay when that keystroke is pressed or the command is executed by longname.

The basic usage is:
    1. `m` (`macro-record`) to begin recording the macro.
    2. Execute a series of commands.
    3. `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

The macro will then be executed everytime the provided keystroke or longname are used. Note: the Alt+keys and the function keys are left unbound; overriding other keys may conflict with existing bindings, now or in the future.

Executing a macro will the series of commands starting on the current row and column on the current sheet.

# The Macros Sheet

- `gm` (`macro-sheet`) to open an index of existing macros.

- `d` to mark macros for deletion.
- `z Ctrl+S` to then commit any changes.
- `Enter` to open the macro in the current row, and view the series of commands composing it.'''


Sheet.addCommand('m', 'macro-record', 'vd.cmdlog.startMacro()', 'record macro')
Sheet.addCommand('gm', 'macro-sheet', 'vd.push(vd.macrosheet)', 'open macros sheet')

vd.addMenuItems('''
    System > Macros sheet > macro-sheet
''')

vd.addGuide('MacrosSheet', MacrosGuide)
