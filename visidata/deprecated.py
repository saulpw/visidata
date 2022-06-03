import functools

from visidata import VisiData, vd
import visidata

alias = visidata.BaseSheet.bindkey

def deprecated(ver, instead=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import traceback

            msg = f'{func.__name__} deprecated since v{ver}'
            if instead:
                msg += f'; use {instead}'
            vd.warning(msg)

            for line in reversed(traceback.extract_stack(limit=6)[:-1]):
                vd.warning(f'    {line.name} at {line.filename}:{line.lineno}')
            vd.warning(f'Deprecated call traceback (most recent last):')
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated('1.6', 'vd instead of vd()')
@VisiData.api
def __call__(vd):
    'Deprecated; use plain "vd"'
    return vd


@deprecated('1.6')
def copyToClipboard(value):
    vd.error("copyToClipboard longer implemented")
    return visidata.clipboard_copy(value)


@deprecated('1.6')
def replayableOption(optname, default, helpstr):
    vd.option(optname, default, helpstr, replay=True)

@deprecated('1.6')
def SubrowColumn(*args, **kwargs):
    return visidata.SubColumnFunc(*args, **kwargs)

@deprecated('1.6')
def DeferredSetColumn(*args, **kwargs):
    return visidata.Column(*args, defer=True, **kwargs)

@deprecated('2.0')
def bindkey_override(keystrokes, longname):
    vd.bindkeys.set(keystrokes, longname)

bindkey = visidata.BaseSheet.bindkey
unbindkey = visidata.BaseSheet.unbindkey

@deprecated('2.0')
@visidata.Sheet.api
def exec_keystrokes(self, keystrokes, vdglobals=None):
    return self.execCommand(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

visidata.Sheet.exec_command = deprecated('2.0')(visidata.Sheet.execCommand)

@deprecated('2.0', 'def open_<filetype> instead')
@VisiData.api
def filetype(vd, ext, constructor):
    'Add constructor to handle the given file type/extension.'
    globals().setdefault('open_'+ext, lambda p,ext=ext: constructor(p.name, source=p, filetype=ext))

@deprecated('2.0', 'Sheet(namepart1, namepart2, ...)')
@VisiData.global_api
def joinSheetnames(vd, *sheetnames):
    'Concatenate sheet names in a standard way'
    return visidata.options.name_joiner.join(str(x) for x in sheetnames)

@deprecated('2.0', 'PyobjSheet')
@VisiData.global_api
def load_pyobj(*names, **kwargs):
    return visidata.PyobjSheet(*names, **kwargs)

@deprecated('2.0', 'PyobjSheet')
@VisiData.global_api
def push_pyobj(name, pyobj):
    vs = visidata.PyobjSheet(name, source=pyobj)
    if vs:
        return vd.push(vs)
    else:
        vd.error("cannot push '%s' as pyobj" % type(pyobj).__name__)

@deprecated('2.1', 'vd.isNumeric instead')
def isNumeric(col):
    return vd.isNumeric(col)

visidata.addGlobals({'load_pyobj': load_pyobj, 'isNumeric': isNumeric})

# The longnames on the left are deprecated for 2.0

alias('edit-cells', 'setcol-input')
alias('fill-nulls', 'setcol-fill')
alias('paste-cells', 'setcol-clipboard')
alias('frequency-rows', 'frequency-summary')
alias('dup-cell', 'dive-cell')
alias('dup-row', 'dive-row')
alias('next-search', 'search-next')
alias('prev-search', 'search-prev')
alias('search-prev', 'searchr-next')
alias('prev-sheet', 'jump-prev')
alias('prev-value', 'go-prev-value')
alias('next-value', 'go-next-value')
alias('prev-selected', 'go-prev-selected')
alias('next-selected', 'go-next-selected')
alias('prev-null', 'go-prev-null')
alias('next-null', 'go-next-null')
alias('page-right', 'go-right-page')
alias('page-left', 'go-left-page')
alias('dive-cell', 'open-cell')
alias('dive-row', 'open-row')
alias('add-sheet', 'open-new')
alias('save-sheets-selected', 'save-selected')
alias('join-sheets', 'join-selected')

# v2.3
alias('show-aggregate', 'memo-aggregate')
#theme('use_default_colors', True, 'curses use default terminal colors')
#option('expand_col_scanrows', 1000, 'number of rows to check when expanding columns (0 = all)')

# 2.6

clean_name = visidata.cleanName

def maybe_clean(s, vs):
    if (vs or visidata.vd).options.clean_names:
        s = visidata.cleanName(s)
    return s

def load_tsv(fn):
    vs = open_tsv(Path(fn))
    yield from vs.iterload()

class VisiDataSheet(visidata.IndexSheet):
    rowtype = 'metasheets'
    precious = False
    columns = [
        visidata.ColumnAttr('items', 'nRows', type=int),
        visidata.ColumnAttr('name', width=0),
        visidata.ColumnAttr('description', width=50),
        visidata.ColumnAttr('command', 'longname', width=0),
        visidata.ColumnAttr('shortcut', 'shortcut_en', width=11),
    ]
    nKeys = 0

    def reload(self):
        self.rows = []
        for vdattr, sheetname, longname, shortcut, desc in [
            ('currentDirSheet', '.', 'open-dir-current', '', 'DirSheet for the current directory'),
            ('sheetsSheet', 'sheets', 'sheets-stack', 'Shift+S', 'current sheet stack'),
            ('allSheetsSheet', 'sheets_all', 'sheets-all', 'g Shift+S', 'all sheets this session'),
            ('allColumnsSheet', 'all_columns', 'columns-all', 'g Shift+C', 'all columns from all sheets'),
            ('cmdlog', 'cmdlog', 'cmdlog-all', 'g Shift+D', 'log of all commands this session'),
            ('globalOptionsSheet', 'options_global', 'open-global', 'Shift+O', 'default option values applying to every sheet'),
            ('recentErrorsSheet', 'errors', 'open-errors', 'Ctrl+E', 'stacktrace of most recent error'),
            ('statusHistorySheet', 'statuses', 'open-statuses', 'Ctrl+P', 'status messages from current session'),
            ('threadsSheet', 'threads', 'open-threads', 'Ctrl+T', 'threads and profiling'),
            ('vdmenu', 'visidata_menu', 'open-vd', 'Shift+V', 'VisiData menu (this sheet)'),
            ('pluginsSheet', 'plugins', 'open-plugins', '', 'VisiData community plugins'),
            ]:
            vs = getattr(vd, vdattr)
            vs.description = desc
            vs.shortcut_en = shortcut
            vs.longname = longname
            if vs is not self:
                vs.ensureLoaded()
            self.addRow(vs)


@VisiData.lazy_property
@deprecated('2.9', 'menu system at top of display')
def vdmenu(vd):
    return VisiDataSheet('visidata_menu', source=vd)


visidata.BaseSheet.addCommand('', 'open-vd', 'vd.push(vd.vdmenu)', 'open VisiData menu: browse list of core sheets')
# NOTE: you cannot use deprecated() with nonfuncs

cancelThread = deprecated('2.6', 'vd.cancelThread')(vd.cancelThread)
status = deprecated('2.6', 'vd.status')(vd.status)
warning = deprecated('2.6', 'vd.warning')(vd.warning)
error = deprecated('2.6', 'vd.error')(vd.error)
debug = deprecated('2.6', 'vd.debug')(vd.debug)
fail = deprecated('2.6', 'vd.fail')(vd.fail)

option = theme = vd.option # deprecated('2.6', 'vd.option')(vd.option)
jointypes = vd.jointypes # deprecated('2.6', 'vd.jointypes')(vd.jointypes)
confirm = deprecated('2.6', 'vd.confirm')(vd.confirm)
launchExternalEditor = deprecated('2.6', 'vd.launchExternalEditor')(vd.launchExternalEditor)
launchEditor = deprecated('2.6', 'vd.launchEditor')(vd.launchEditor)
exceptionCaught = deprecated('2.6', 'vd.exceptionCaught')(vd.exceptionCaught)
openSource = deprecated('2.6', 'vd.openSource')(vd.openSource)
globalCommand = visidata.BaseSheet.addCommand
