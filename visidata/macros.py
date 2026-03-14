import re
from copy import copy
from functools import wraps

from visidata.cmdlog import CommandLog, CommandLogJsonl
from visidata import vd, UNLOADED, asyncthread, vlen
from visidata import IndexSheet, VisiData, Sheet, Path, VisiDataMetaSheet, Column, ItemColumn, AttrColumn, BaseSheet

vd.macroMode = None  # CommandLog
vd.macrobindings = {}

MACRO_PARAM_RE = re.compile(r'\{(\w+)(?:=([^}]*))?\}')


vd.macros = vd.StoredList(name='macros')


class MacroSheet(IndexSheet):
    guide= '''
        # Macros Sheet
        This is a list of user-defined macros.

        - `Enter` to open the current macro.
        - `d` to mark macro for delete; `z Ctrl+S` to commit.
        - Edit `keystroke` to bind/change a keystroke for a macro.
        - Edit `input` or `col` to use `{param}` or `{param=default}` for parameters.
    '''
    columns = [
        AttrColumn('binding'),
        AttrColumn('keystroke'),
        AttrColumn('helpstr'),
        Column('num_commands', type=vlen, width=0),
        AttrColumn('source'),
    ]
    rowtype = 'macros'  # rowdef: CommandLogJsonl
    defer = True
    nKeys = 1

    def iterload(self):
        yield from vd.macrobindings.values()

    def commitDeleteRow(self, row):
        binding = row.binding
        keystroke = getattr(row, 'keystroke', '')

        # Remove from macrobindings
        del vd.macrobindings[binding]

        # Remove command registration and key bindings
        if vd.isLongname(binding):
            BaseSheet.removeCommand('', binding)
            if keystroke:
                BaseSheet.unbindkey(keystroke)
        else:
            BaseSheet.removeCommand(binding, f'exec-{row.name}')

        # Delete source file
        vd.callNoExceptions(Path(row.source).unlink)

    @asyncthread
    def putChanges(self):
        self.commitDeletes()  #1569  apply deletes early for saveSheets below

        vd.sync(vd.saveSheets(self.source, self, confirm_overwrite=False))
        self._deferredDels.clear()
        vd.reloadMacros()
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

    cmdlog = vd.macrobindings[binding]

    # #2785: check for parameterized inputs
    params = {}  # name -> default
    for row in cmdlog.rows:
        for field in ('input', 'col'):
            val = getattr(row, field, '')
            if val:
                for m in MACRO_PARAM_RE.finditer(str(val)):
                    name, default = m.group(1), m.group(2)
                    if name not in params:
                        params[name] = default or ''

    if params:
        param_values = vd.inputMultiple(**{
            name: dict(prompt=f'{name}: ', value=default)
            for name, default in params.items()
        })

        cmdlog = copy(cmdlog)
        cmdlog.rows = []
        for row in vd.macrobindings[binding].rows:
            row = copy(row)
            for field in ('input', 'col'):
                val = getattr(row, field, '')
                if val:
                    setattr(row, field, MACRO_PARAM_RE.sub(
                        lambda m: param_values.get(m.group(1), m.group(0)),
                        str(val)))
            cmdlog.rows.append(row)

    vd.replay_sync(cmdlog)
    vd.macroMode = mm


@VisiData.api
def setMacro(vd, ks:str, vs, helpstr='', keystroke=''):
    'Set *ks* which is either a keystroke or a longname to run the cmdlog in *vs*.'
    ks = vd.prettykeys(ks)
    keystroke = vd.prettykeys(keystroke) if keystroke else ''
    vs.binding = ks
    vs.helpstr = helpstr
    vs.keystroke = keystroke
    vd.macrobindings[ks] = vs
    old_module = vd.importingModule
    vd.importingModule = 'macros'
    try:
        if vd.isLongname(ks):
            BaseSheet.addCommand('', ks, f'runMacro("{ks}")', helpstr)
            if keystroke:  #2784
                BaseSheet.bindkey(keystroke, ks)
        else:
            BaseSheet.addCommand(ks, f'exec-{vs.name}', f'runMacro("{ks}")', helpstr)
    finally:
        vd.importingModule = old_module


@CommandLogJsonl.api
def saveMacro(self, rows, ks, keystroke=''):
        vs = copy(self)
        vs.rows = rows
        macropath = Path(vd.fnSuffix(str(Path(vd.options.visidata_dir)/ks)))
        vd.save_vdj(macropath, vs)
        vd.status(f'{ks} saved to {macropath}')
        vd.setMacro(ks, vs, keystroke=keystroke)
        vd.macros.append(dict(binding=ks, source=str(macropath), helpstr='', keystroke=keystroke))
        vd.reloadMacros()
        vd.macrosheet.reload()


# needs to happen before, because the original afterexecsheet resets vd.activecommand to None
@CommandLogJsonl.before
def afterExecSheet(cmdlog, sheet, escaped, err):
    if not vd.macroMode: return
    if not vd.activeCommand: return
    if vd.activeCommand.longname == 'macro-record': return

    if vd.activeCommand.replayable:
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
            ks = vd.prettykeys(ks)
            while ks in vd.macrobindings:
                ks = vd.prettykeys(vd.input(f'{ks} already in use; set macro to keybinding: '))

            keystroke = ''
            if vd.isLongname(ks):  #2784
                keystroke = vd.input('bind keystroke (Enter to skip): ', help='''
                    # Bind a keystroke to this macro (optional)
                    Spell out a keystroke (like `Alt+b`) or press `Enter` to skip.
                    - Press `Ctrl+N` and then press another keystroke to spell that keystroke.
                ''')
                while keystroke:
                    keystroke = vd.prettykeys(keystroke)
                    existing = vd.bindkeys._get(keystroke, BaseSheet)
                    if not existing:
                        break
                    keystroke = vd.input(f'{keystroke} already bound to {existing}; enter keystroke (Enter to skip): ')

            vd.cmdlog.saveMacro(vd.macroMode.rows, ks, keystroke=keystroke)
        finally:
            vd.macroMode = None
    else:
        ks = vd.sheet.revbinds.get('macro-record', ['m'])[0]  #2776
        vd.status(f"recording macro; stop recording with `{ks}`")
        vd.macroMode = CommandLogJsonl('current_macro', rows=[])


@VisiData.before
@asyncthread
def run(vd, *args, **kwargs):
    vd.reloadMacros()


@VisiData.api
def reloadMacros(vd):
    vd.macros.reload()
    for r in vd.macros:
        p = Path(r.source)
        if not p.is_absolute():
            p = vd.macros.path.parent / r.source
        vs = vd.loadMacro(p)
        if vs:
            vd.setMacro(r.binding, vs, getattr(r, 'helpstr', ''), keystroke=getattr(r, 'keystroke', ''))


Sheet.addCommand('m', 'macro-record', 'vd.cmdlog.startMacro()', 'start/stop macro recording', replay=False)
Sheet.addCommand('gm', 'macro-sheet', 'vd.push(vd.macrosheet)', 'open an index of existing macros')

vd.addMenuItems('''
    System > Record macro > macro-record
    System > Macros sheet > macro-sheet
''')
