import functools

from visidata import VisiData, vd
import visidata

def deprecated_alias(depver, *args, **kwargs):
    # expand this to create cmd
    # with cmd.deprecated=depver
    return visidata.BaseSheet.bindkey(*args, **kwargs)

@VisiData.api
def deprecated_warn(vd, funcname, ver, instead):
    import traceback

    msg = f'{funcname} deprecated since v{ver}'
    if instead:
        msg += f'; use {instead}'

    vd.warning(msg)

    if vd.options.debug:
        for line in reversed(traceback.extract_stack(limit=7)[:-2]):
            vd.warning(f'    {line.name} at {line.filename}:{line.lineno}')
        vd.warning(f'Deprecated call traceback (most recent last):')


def deprecated(ver, instead='', check=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            vd.deprecated_warn(wrapper.__name__, ver, instead)
            return func(*args, **kwargs)

        if check and hasattr(func, '_extensible_api'):
            vd.error(f"{func.__name__}: @deprecated applied in wrong order")  #2623

        return wrapper
    return decorator


def _deprecated_api(ver, instead=''):
    'Decorator to deliberately wrap non-deprecated .api functions as a deprecated global function.  Use @deprecated instead, except in deprecated.py.'
    return deprecated(ver, instead, check=False)


@VisiData.api
@deprecated('1.6', 'vd instead of vd()')
def __call__(vd):
    'Deprecated; use plain "vd"'
    return vd


@deprecated('1.6')
def copyToClipboard(value):
    vd.error("copyToClipboard no longer implemented")
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

@visidata.Sheet.api
@deprecated('2.0')
def exec_keystrokes(self, keystrokes, vdglobals=None):
    return self.execCommand(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

visidata.Sheet.exec_command = deprecated('2.0')(visidata.Sheet.execCommand)

@VisiData.api
@deprecated('2.0', 'def open_<filetype> instead')
def filetype(vd, ext, constructor):
    'Add constructor to handle the given file type/extension.'
    globals().setdefault('open_'+ext, lambda p,ext=ext: constructor(p.base_stem, source=p, filetype=ext))

@VisiData.global_api
@deprecated('2.0', 'Sheet(namepart1, namepart2, ...)')
def joinSheetnames(vd, *sheetnames):
    'Concatenate sheet names in a standard way'
    return visidata.options.name_joiner.join(str(x) for x in sheetnames)

@VisiData.global_api
@deprecated('2.0', 'PyobjSheet')
def load_pyobj(*names, **kwargs):
    return visidata.PyobjSheet(*names, **kwargs)

@VisiData.global_api
@deprecated('2.0', 'PyobjSheet')
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

deprecated_alias('2.0', 'edit-cells', 'setcol-input')
deprecated_alias('2.0', 'fill-nulls', 'setcol-fill')
deprecated_alias('2.0', 'paste-cells', 'setcol-clipboard')
deprecated_alias('2.0', 'frequency-rows', 'frequency-summary')
deprecated_alias('2.0', 'dup-cell', 'dive-cell')
deprecated_alias('2.0', 'dup-row', 'dive-row')
deprecated_alias('2.0', 'next-search', 'search-next')
deprecated_alias('2.0', 'prev-search', 'search-prev')
deprecated_alias('2.0', 'search-prev', 'searchr-next')
deprecated_alias('2.0', 'prev-sheet', 'jump-prev')
deprecated_alias('2.0', 'prev-value', 'go-prev-value')
deprecated_alias('2.0', 'next-value', 'go-next-value')
deprecated_alias('2.0', 'prev-selected', 'go-prev-selected')
deprecated_alias('2.0', 'next-selected', 'go-next-selected')
deprecated_alias('2.0', 'prev-null', 'go-prev-null')
deprecated_alias('2.0', 'next-null', 'go-next-null')
deprecated_alias('2.0', 'page-right', 'go-right-page')
deprecated_alias('2.0', 'page-left', 'go-left-page')
deprecated_alias('2.0', 'dive-cell', 'open-cell')
deprecated_alias('2.0', 'dive-row', 'open-row')
deprecated_alias('2.0', 'add-sheet', 'open-new')
deprecated_alias('2.0', 'save-sheets-selected', 'save-selected')
deprecated_alias('2.0', 'join-sheets', 'join-selected')
deprecated_alias('2.0', 'dive-rows', 'dive-selected')

# v2.3
deprecated_alias('2.3', 'show-aggregate', 'memo-aggregate')
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

cancelThread = _deprecated_api('2.6', 'vd.cancelThread')(vd.cancelThread)
status = _deprecated_api('2.6', 'vd.status')(vd.status)
warning = _deprecated_api('2.6', 'vd.warning')(vd.warning)
error = _deprecated_api('2.6', 'vd.error')(vd.error)
debug = _deprecated_api('2.6', 'vd.debug')(vd.debug)
fail = _deprecated_api('2.6', 'vd.fail')(vd.fail)

option = theme = vd.option # deprecated('2.6', 'vd.option')(vd.option)
jointypes = vd.jointypes # deprecated('2.6', 'vd.jointypes')(vd.jointypes)
confirm = _deprecated_api('2.6', 'vd.confirm')(vd.confirm)
launchExternalEditor = _deprecated_api('2.6', 'vd.launchExternalEditor')(vd.launchExternalEditor)
launchEditor = _deprecated_api('2.6', 'vd.launchEditor')(vd.launchEditor)
exceptionCaught = _deprecated_api('2.6', 'vd.exceptionCaught')(vd.exceptionCaught)
openSource = _deprecated_api('2.6', 'vd.openSource')(vd.openSource)
globalCommand = visidata.BaseSheet.addCommand
visidata.Sheet.StaticColumn = _deprecated_api('2.11', 'Sheet.freeze_col')(visidata.Sheet.freeze_col)
#visidata.Path.open_text = deprecated('3.0', 'visidata.Path.open')(visidata.Path.open)  # undeprecated in 3.1

vd.sysclip_value = _deprecated_api('3.0', 'vd.sysclipValue')(vd.sysclipValue)

def itemsetter(i):
    def g(obj, v):
        obj[i] = v
    return g


vd.optalias('force_valid_colnames', 'clean_names')
vd.optalias('dir_recurse', 'dir_depth', 100000)
vd.optalias('confirm_overwrite', 'overwrite', 'confirm')
vd.optalias('show_graph_labels', 'disp_graph_labels')
vd.optalias('zoom_incr', 'disp_zoom_incr')

deprecated_alias('3.0', 'visibility-sheet', 'toggle-multiline')
deprecated_alias('3.0', 'visibility-col', 'toggle-multiline')

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

deprecated_alias('3.0', 'open-inputs', 'open-input-history')

#vd.option('plugins_url', 'https://visidata.org/plugins/plugins.jsonl', 'source of plugins sheet')

@visidata.VisiData.api
def inputRegexSubstOld(vd, prompt):
    'Input regex transform via oneliner (separated with `/`).  Return parsed transformer as dict(before=, after=).'
    rex = vd.inputRegex(prompt, type='regex-subst')
    before, after = vd.parse_sed_transform(rex)
    return dict(before=before, after=after)


visidata.Sheet.addCommand('', 'addcol-subst', 'addColumnAtCursor(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, **inputRegexSubstOld("transform column by regex: "))))', 'add column derived from current column, replacing regex with subst (may include \1 backrefs)', deprecated='3.0')
visidata.Sheet.addCommand('', 'setcol-subst', 'setValuesFromRegex([cursorCol], someSelectedRows, **inputRegexSubstOld("transform column by regex: "))', 'regex/subst - modify selected rows in current column, replacing regex with subst, (may include backreferences \\1 etc)', deprecated='3.0')
visidata.Sheet.addCommand('', 'setcol-subst-all', 'setValuesFromRegex(visibleCols, someSelectedRows, **inputRegexSubstOld(f"transform {nVisibleCols} columns by regex: "))', 'modify selected rows in all visible columns, replacing regex with subst (may include \\1 backrefs)', deprecated='3.0')

visidata.Sheet.addCommand('', 'split-col', 'addRegexColumns(makeRegexSplitter, cursorCol, inputRegex("split regex: ", type="regex-split"))', 'Add new columns from regex split', deprecated='3.0')
visidata.Sheet.addCommand('', 'capture-col', 'addRegexColumns(makeRegexMatcher, cursorCol, inputRegex("capture regex: ", type="regex-capture"))', 'add new column from capture groups of regex; requires example row', deprecated='3.0')

#vd.option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to', sheettype=None)
#BaseSheet.bindkey('KEY_BACKSPACE', 'menu-help')

@visidata.Column.api
@deprecated('3.0', 'vd.callNoExceptions(col.setValue, row, value)')
def setValueSafe(self, row, value):
    'setValue and ignore exceptions.'
    return vd.callNoExceptions(self.setValue, row, value)

@visidata.BaseSheet.api
@deprecated('3.0', 'vd.callNoExceptions(sheet.checkCursor)')
def checkCursorNoExceptions(sheet):
    return vd.callNoExceptions(sheet.checkCursor)

@VisiData.api
@deprecated('3.1', 'vd.memoValue(name, value, displayvalue)')
def memo(vd, name, col, row):
    return vd.memoValue(name, col.getTypedValue(row), col.getDisplayValue(row))

deprecated_alias('3.1', 'view-cell', 'pyobj-cell')

vd.optalias('textwrap_cells', 'disp_wrap_max_lines', 3) # wordwrap text for multiline rows

@visidata.TableSheet.api
@deprecated('3.1', 'sheet.rowname(row)')
def keystr(sheet, row):
    return sheet.rowname(row)

vd.optalias('color_refline', 'color_graph_refline') # color_refline was used in v3.1 by mistake

@visidata.TableSheet.api
@deprecated('3.2', '[self.unsetKeys([c]) if c.keycol else self.setKeys([c]) for c in cols]')
def toggleKeys(self, cols):
    for col in cols:
        if col.keycol:
            self.unsetKeys([col])
        else:
            self.setKeys([col])

vd.optalias('disp_pixel_random', 'disp_graph_pixel_random')  #2661

vd.addGlobals(deprecated_warn=deprecated_warn)
