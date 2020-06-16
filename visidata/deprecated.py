from visidata import VisiData
import visidata

alias = visidata.BaseSheet.bindkey

def deprecated(ver):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # ideally would include a stacktrace
            visidata.warning(f'{func.__name__} deprecated since v{ver}')
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated('1.6')
@VisiData.api
def __call__(vd):
    'Deprecated; use plain "vd"'
    return vd


@deprecated('1.6')
def copyToClipboard(value):
    return visidata.clipboard().copy(value)


@deprecated('1.6')
def replayableOption(optname, default, helpstr):
    option(optname, default, helpstr, replay=True)

@deprecated('1.6')
def SubrowColumn(*args, **kwargs):
    return visidata.SubColumnFunc(*args, **kwargs)

@deprecated('1.6')
def DeferredSetColumn(*args, **kwargs):
    return Column(*args, defer=True, **kwargs)

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

# The longnames on the left are deprecated for 2.0

alias('edit-cells', 'setcol-input')
alias('fill-nulls', 'setcol-fill')
alias('paste-cells', 'setcol-clipboard')
alias('frequency-rows', 'frequency-summary')
alias('dup-cell', 'dive-cell')
alias('dup-row', 'dive-row')
alias('next-search', 'search-next')
alias('prev-search', 'search-prev')
alias('prev-sheet', 'jump-prev')
alias('prev-value', 'go-prev-value')
alias('next-value', 'go-next-value')
alias('prev-selected', 'go-prev-selected')
alias('next-selected', 'go-next-selected')
alias('prev-null', 'go-prev-null')
alias('next-null', 'go-next-null')
alias('page-right', 'go-right-page')
alias('page-left', 'go-left-page')
alias('statuses', 'open-statuses')
alias('status', 'show-status')
alias('dive-cell', 'open-cell')
alias('dive-row', 'open-row')
alias('add-sheet', 'open-new')
