import functools

from visidata import VisiData, vd
import visidata

alias = visidata.BaseSheet.bindkey

def deprecated_warn(func, ver, instead):
    import traceback

    msg = f'{func.__name__} deprecated since v{ver}'
    if instead:
        msg += f'; use {instead}'

    vd.warning(msg)

    if vd.options.debug:
        for line in reversed(traceback.extract_stack(limit=7)[:-2]):
            vd.warning(f'    {line.name} at {line.filename}:{line.lineno}')
        vd.warning(f'Deprecated call traceback (most recent last):')


def deprecated(ver, instead=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            deprecated_warn(func, ver, instead)
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
    globals().setdefault('open_'+ext, lambda p,ext=ext: constructor(p.base_stem, source=p, filetype=ext))

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
alias('dive-rows', 'dive-selected')

# v2.3
alias('show-aggregate', 'memo-aggregate')
#theme('use_default_colors', True, 'curses use default terminal colors')
#option('expand_col_scanrows', 1000, 'number of rows to check when expanding columns (0 = all)')

# 2.6

def clean_name(s):
    return visidata.vd.cleanName(s)

def maybe_clean(s, vs):
    if (vs or visidata.vd).options.clean_names:
        s = visidata.vd.cleanName(s)
    return s

def load_tsv(fn):
    vs = open_tsv(Path(fn))
    yield from vs.iterload()

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
visidata.Sheet.StaticColumn = deprecated('2.11', 'Sheet.freeze_col')(visidata.Sheet.freeze_col)
#visidata.Path.open_text = deprecated('3.0', 'visidata.Path.open')(visidata.Path.open)  # undeprecated in 3.1

vd.sysclip_value = deprecated('3.0', 'vd.sysclipValue')(vd.sysclipValue)

def itemsetter(i):
    def g(obj, v):
        obj[i] = v
    return g


vd.optalias('force_valid_colnames', 'clean_names')
vd.optalias('dir_recurse', 'dir_depth', 100000)
vd.optalias('confirm_overwrite', 'overwrite', 'confirm')
vd.optalias('show_graph_labels', 'disp_graph_labels')
vd.optalias('zoom_incr', 'disp_zoom_incr')

alias('visibility-sheet', 'toggle-multiline')
alias('visibility-col', 'toggle-multiline')

def clean_to_id(s):
    return visidata.vd.cleanName(s)

@deprecated('3.0', 'use try/finally')
class OnExit:
    '"with OnExit(func, ...):" calls func(...) when the context is exited'
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            vd.exceptionCaught(e)

alias('open-inputs', 'open-input-history')

#vd.option('plugins_url', 'https://visidata.org/plugins/plugins.jsonl', 'source of plugins sheet')

@visidata.VisiData.api
def inputRegexSubstOld(vd, prompt):
    'Input regex transform via oneliner (separated with `/`).  Return parsed transformer as dict(before=, after=).'
    rex = vd.inputRegex(prompt, type='regex-subst')
    before, after = vd.parse_sed_transform(rex)
    return dict(before=before, after=after)


visidata.Sheet.addCommand('', 'addcol-subst', 'addColumnAtCursor(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, **inputRegexSubstOld("transform column by regex: "))))', 'add column derived from current column, replacing regex with subst (may include \1 backrefs)', deprecated=True)
visidata.Sheet.addCommand('', 'setcol-subst', 'setValuesFromRegex([cursorCol], someSelectedRows, **inputRegexSubstOld("transform column by regex: "))', 'regex/subst - modify selected rows in current column, replacing regex with subst, (may include backreferences \\1 etc)', deprecated=True)
visidata.Sheet.addCommand('', 'setcol-subst-all', 'setValuesFromRegex(visibleCols, someSelectedRows, **inputRegexSubstOld(f"transform {nVisibleCols} columns by regex: "))', 'modify selected rows in all visible columns, replacing regex with subst (may include \\1 backrefs)', deprecated=True)

visidata.Sheet.addCommand('', 'split-col', 'addRegexColumns(makeRegexSplitter, cursorCol, inputRegex("split regex: ", type="regex-split"))', 'Add new columns from regex split', deprecated=True)
visidata.Sheet.addCommand('', 'capture-col', 'addRegexColumns(makeRegexMatcher, cursorCol, inputRegex("capture regex: ", type="regex-capture"))', 'add new column from capture groups of regex; requires example row', deprecated=True)

#vd.option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to', sheettype=None)
#BaseSheet.bindkey('KEY_BACKSPACE', 'menu-help')

@deprecated('3.0', 'vd.callNoExceptions(col.setValue, row, value)')
@visidata.Column.api
def setValueSafe(self, row, value):
    'setValue and ignore exceptions.'
    return vd.callNoExceptions(self.setValue, row, value)

@deprecated('3.0', 'vd.callNoExceptions(sheet.checkCursor)')
@visidata.BaseSheet.api
def checkCursorNoExceptions(sheet):
    return vd.callNoExceptions(sheet.checkCursor)

@deprecated('3.1', 'vd.memoValue(name, value, displayvalue)')
@VisiData.api
def memo(vd, name, col, row):
    return vd.memoValue(name, col.getTypedValue(row), col.getDisplayValue(row))

alias('view-cell', 'pyobj-cell')

vd.optalias('textwrap_cells', 'disp_wrap_max_lines', 3) # wordwrap text for multiline rows

@deprecated('3.1', 'sheet.rowname(row)')
@visidata.TableSheet.api
def keystr(sheet, row):
    return sheet.rowname(row)
