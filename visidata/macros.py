from visidata import *
from functools import wraps

from visidata.cmdlog import CommandLog, CommandLogJsonl

vd.macroMode = None
vd.macrobindings = {}

@VisiData.lazy_property
def macrosheet(vd):
    macrospath = Path(os.path.join(options.visidata_dir, 'macros.tsv'))
    macrosheet = vd.loadInternalSheet(TsvSheet, macrospath, columns=(ColumnItem('command', 0), ColumnItem('filename', 1))) or vd.error('error loading macros')

    real_macrosheet = IndexSheet('user_macros', rows=[], source=macrosheet)
    for ks, fn in macrosheet.rows:
        fp = Path(fn)
        if fp.ext == 'vd':
            vs = vd.loadInternalSheet(CommandLog, fp)
        elif fp.ext == 'vdj':
            vs = vd.loadInternalSheet(CommandLogJsonl, fp)
        else:
            vd.warning(f'failed to load macro {fn}')
            continue
        vd.status(f"setting {ks}")
        setMacro(ks, vs)
        real_macrosheet.addRow(vs)

    return real_macrosheet

@VisiData.api
def runMacro(vd, macro):
    vd.replay_sync(macro, live=True)

def setMacro(ks, vs):
    vd.macrobindings[ks] = vs
    if vd.isLongname(ks):
        BaseSheet.addCommand('', ks, 'runMacro(vd.macrobindings[longname])')
    else:
        BaseSheet.addCommand(ks, vs.name, 'runMacro(vd.macrobindings[keystrokes])')


@CommandLogJsonl.api
def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = rows
        macropath = Path(vd.fnSuffix(options.visidata_dir+"macro"))
        vd.save_vdj(macropath, vs)
        setMacro(ks, vs)
        vd.macrosheet.source.append_tsv_row((ks, macropath))
        vd.macrosheet.addRow(vd.loadInternalSheet(CommandLogJsonl, macropath))

@CommandLogJsonl.api
@wraps(CommandLogJsonl.afterExecSheet)
def afterExecSheet(cmdlog, sheet, escaped, err):
    if vd.macroMode and (vd.activeCommand is not None) and (vd.activeCommand is not UNLOADED):
        cmd = copy(vd.activeCommand)
        cmd.row = cmd.col = cmd.sheet = ''
        vd.macroMode.addRow(cmd)

    # the following needs to happen at the end, bc
    # once cmdlog.afterExecSheet.__wrapped__ runs, vd.activeCommand resets to None
    cmdlog.afterExecSheet.__wrapped__(cmdlog, sheet, escaped, err)

@CommandLogJsonl.api
def startMacro(cmdlog):
    if vd.macroMode:
        ks = vd.input('save macro for keystroke: ')
        vd.cmdlog.saveMacro(vd.macroMode.rows, ks)
        vd.macroMode = None
    else:
        vd.status("recording macro")
        vd.macroMode = CommandLogJsonl('current_macro', rows=[])

@VisiData.before
def run(vd, *args, **kwargs):
    vd.macrosheet


Sheet.addCommand('m', 'macro-record', 'vd.cmdlog.startMacro()', 'record macro')
Sheet.addCommand('gm', 'macro-sheet', 'vd.push(vd.macrosheet)', 'open macros sheet')
