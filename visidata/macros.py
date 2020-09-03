from visidata import *


@VisiData.lazy_property
def macrosheet(vd):
    macrospath = Path(os.path.join(options.visidata_dir, 'macros.tsv'))
    macrosheet = vd.loadInternalSheet(TsvSheet, macrospath, columns=(ColumnItem('command', 0), ColumnItem('filename', 1))) or vd.error('error loading macros')

    for ks, fn in macrosheet.rows:
        vs = vd.loadInternalSheet(CommandLog, Path(fn))
        setMacro(ks, vs)

    return macrosheet

def setMacro(ks, vs):
    vd.bindkeys.set(ks, vs.name, 'override')
    vd.commands.set(vs.name, vs, 'override')


@CommandLog.api
def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = self.selectedRows
        macropath = Path(fnSuffix(options.visidata_dir+"macro"))
        vd.save_vd(macropath, vs)
        setMacro(ks, vs)
        append_tsv_row(vd.macrosheet, (ks, macropath))


CommandLog.addCommand('z^D', 'save-macro', 'sheet.saveMacro(selectedRows or fail("no rows selected"), input("save macro for keystroke: "))', 'save selected rows to macro mapped to keystroke')
