from visidata import *


@VisiData.cached_property
def macrosheet(vd):
    macrospath = Path(os.path.join(options.visidata_dir, 'macros.tsv'))
    macrosheet = loadInternalSheet(TsvSheet, macrospath, columns=(ColumnItem('command', 0), ColumnItem('filename', 1))) or error('error loading macros')

    for ks, fn in macrosheet.rows:
        vs = loadInternalSheet(CommandLog, Path(fn))
        setMacro(ks, vs)

    return macrosheet

def setMacro(ks, vs):
    bindkeys.set(ks, vs.name, 'override')
    commands.set(vs.name, vs, 'override')


@CommandLog.api
def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = self.selectedRows
        macropath = Path(fnSuffix(options.visidata_dir+"macro-{0}.vd"))
        save_vd(macropath, vs)
        setMacro(ks, vs)
        append_tsv_row(vd.macrosheet, (ks, macropath.resolve()))


CommandLog.addCommand('z^S', 'save-macro', 'sheet.saveMacro(selectedRows or fail("no rows selected"), input("save macro for keystroke: "))')
