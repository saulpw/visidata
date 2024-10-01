from copy import copy
from functools import wraps

from visidata.cmdlog import CommandLog, CommandLogJsonl
from visidata import vd, UNLOADED, asyncthread, vlen
from visidata import IndexSheet, VisiData, Sheet, Path, VisiDataMetaSheet, Column, ItemColumn, AttrColumn, BaseSheet

vd.macroMode = None  # CommandLog
vd.macrobindings = {}


vd.macros = vd.StoredList(name='macros')


class MacroSheet(IndexSheet):
    guide= '''
        # Macros Sheet
        This is a list of user-defined macros.

        - `Enter` to open the current macro.
        - `d` to mark macro for delete; `z Ctrl+S` to commit.
    '''
    columns = [
        AttrColumn('binding'),
        Column('num_commands', type=vlen, width=0),
        AttrColumn('source'),
    ]
    rowtype = 'macros'  # rowdef: CommandLogJsonl
    defer = True
    nKeys = 1

    def iterload(self):
        yield from vd.macrobindings.values()

    def commitDeleteRow(self, row):
        del vd.macrobindings[row.binding]
        vd.callNoExceptions(Path(row.source).unlink)

    @asyncthread
    def putChanges(self):
        self.commitDeletes()  #1569  apply deletes early for saveSheets below

        vd.saveSheets(self.source, self, confirm_overwrite=False)
        self._deferredDels.clear()
        self.reload()

    def newRow(self):
        vd.fail('add macros with `m` instead')


@VisiData.lazy_property
def macrosheet(vd):
    return MacroSheet('user_macros', source=vd.macros.path)


@VisiData.api
def loadMacro(vd, p:Path):
    if p.exists():
        if p.ext == 'vd':
            vs = CommandLog(p.base_stem, source=p)
            vs.ensureLoaded()
            return vs
        elif p.ext == 'vdj':
            vs = CommandLogJsonl(p.base_stem, source=p)
            vs.ensureLoaded()
            return vs

    vd.warning(f'failed to load macro {p}')


@VisiData.api
def runMacro(vd, binding:str):
    mm = vd.macroMode
    vd.macroMode = None
    vd.replay_sync(vd.macrobindings[binding])
    vd.macroMode = mm


@VisiData.api
def setMacro(vd, ks:str, vs):
    'Set *ks* which is either a keystroke or a longname to run the cmdlog in *vs*.'
    vs.binding = ks
    vd.macrobindings[ks] = vs
    if vd.isLongname(ks):
        BaseSheet.addCommand('', ks, f'runMacro("{ks}")')
    else:
        BaseSheet.addCommand(ks, f'exec-{vs.name}', f'runMacro("{ks}")')


@CommandLogJsonl.api
def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = rows
        macropath = Path(vd.fnSuffix(str(Path(vd.options.visidata_dir)/ks)))
        vd.save_vdj(macropath, vs)
        vd.status(f'{ks} saved to {macropath}')
        vd.setMacro(ks, vs)
        vd.macros.append(dict(binding=ks, source=str(macropath)))
        vd.reloadMacros()
        vd.macrosheet.reload()


# needs to happen before, because the original afterexecsheet resets vd.activecommand to None
@CommandLogJsonl.before
def afterExecSheet(cmdlog, sheet, escaped, err):
    if not vd.macroMode: return
    if not vd.activeCommand: return
    if vd.activeCommand.longname == 'macro-record': return

    cmd = copy(vd.activeCommand)
    cmd.sheet = ''
    vd.macroMode.addRow(cmd)


@CommandLogJsonl.api
def startMacro(cmdlog):
    if not Path(vd.options.visidata_dir).is_dir():
        vd.fail(f'create {vd.options.visidata_dir} to save macros')
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
    vd.reloadMacros()


@VisiData.api
def reloadMacros(vd):
    vd.macros.reload()
    for r in vd.macros:
        vs = vd.loadMacro(Path(r.source))
        if vs:
            vd.setMacro(r.binding, vs)


Sheet.addCommand('m', 'macro-record', 'vd.cmdlog.startMacro()', 'start/stop macro recording', replay=False)
Sheet.addCommand('gm', 'macro-sheet', 'vd.push(vd.macrosheet)', 'open an index of existing macros')

vd.addMenuItems('''
    System > Record macro > macro-record
    System > Macros sheet > macro-sheet
''')
