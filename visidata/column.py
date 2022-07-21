from copy import copy
import collections
import string
import itertools
import threading
import re
import time
import json

from visidata import options, anytype, stacktrace, vd
from visidata import asyncthread, dispwidth, clipstr, iterchars
from visidata import wrapply, TypedWrapper, TypedExceptionWrapper
from visidata import Extensible, AttrDict, undoAttrFunc

class InProgress(Exception):
    @property
    def stacktrace(self):
        return  ['calculation in progress']

INPROGRESS = TypedExceptionWrapper(None, exception=InProgress())  # sentinel

vd.option('col_cache_size', 0, 'max number of cache entries in each cached column')
vd.option('clean_names', False, 'clean column/sheet names to be valid Python identifiers', replay=True)

__all__ = [
    'clean_to_id',
    'Column',
    'setitem',
    'getattrdeep',
    'setattrdeep',
    'getitemdef',
    'ColumnAttr', 'AttrColumn',
    'ColumnItem', 'ItemColumn',
    'SettableColumn',
    'SubColumnFunc',
    'SubColumnItem',
    'SubColumnAttr',
    'ColumnExpr', 'ExprColumn',
    'DisplayWrapper',
]


class DisplayWrapper:
    def __init__(self, value=None, *, display=None, note=None, notecolor=None, error=None):
        self.value = value      # actual value (any type)
        self.display = display  # displayed string
        self.note = note        # single unicode character displayed in cell far right
        self.notecolor = notecolor  # configurable color name (like 'color_warning')
        self.error = error      # list of strings for stacktrace

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return self.value == other


def clean_to_id(s):  # [Nas Banov] https://stackoverflow.com/a/3305731
    return re.sub(r'\W|^(?=\d)', '_', str(s)).strip('_')


def _default_colnames():
    'A B C .. Z AA AB .. ZZ AAA .. to infinity'
    i=0
    while True:
        i += 1
        for x in itertools.product(string.ascii_uppercase, repeat=i):
            yield ''.join(x)

default_colnames = _default_colnames()


class Column(Extensible):
    '''Base class for all column types.

        - *name*: name of this column.
        - *type*: ``anytype str int float date`` or other type-like conversion function.
        - *cache*: cache behavior

           - ``False`` (default): getValue never caches; calcValue is always called.
           - ``True``: getValue maintains a cache of ``options.col_cache_size``.
           - ``"async"``: ``getValue`` launches thread for every uncached result, returns invalid value until cache entry available.
        - *width*: == 0 if hidden, None if auto-compute next time.
        - *height*: max height, None/0 to auto-compute for each row.
        - *fmtstr*: format string as applied by column type.
        - *getter*: default calcValue calls ``getter(col, row)``.
        - *setter*: default putValue calls ``setter(col, row, val)``.
        - *kwargs*: other attributes to be set on this column.
    '''
    def __init__(self, name=None, *, type=anytype, cache=False, **kwargs):
        self.sheet = None     # owning Sheet, set in .recalc() via Sheet.addColumn
        if name is None:
            name = next(default_colnames)
        self.name = str(name) # display visible name
        self.fmtstr = ''      # by default, use str()
        self._type = type     # anytype/str/int/float/date/func
        self.getter = lambda col, row: row
        self.setter = lambda col, row, value: vd.fail(col.name+' column cannot be changed')
        self._width = None    # == 0 if hidden, None if auto-compute next time
        self.hoffset = 0      # starting horizontal (char) offset of displayed column value
        self.voffset = 0      # starting vertical (line) offset of displayed column value
        self.height = 1       # max height, None/0 to auto-compute for each row
        self.keycol = 0       # keycol index (or 0 if not key column)
        self.expr = None      # Column-type-dependent parameter
        self.formatter = ''

        self.setCache(cache)
        for k, v in kwargs.items():
            setattr(self, k, v)  # instead of __dict__.update(kwargs) to invoke property.setters

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.keycol = 0   # column copies lose their key status
        if self._cachedValues is not None:
            ret._cachedValues = collections.OrderedDict()  # an unrelated cache for copied columns
        return ret

    def __deepcopy__(self, memo):
        return self.__copy__()  # no separate deepcopy

    def __getstate__(self):
        d = {k:getattr(self, k) for k in 'name width height expr keycol formatter fmtstr voffset hoffset aggstr'.split() if hasattr(self, k)}
        d['type'] = self.type.__name__
        return d

    def __setstate__(self, d):
        for attr, v in d.items():
            setattr(self, attr, v)

    def recalc(self, sheet=None):
        'Reset column cache, attach column to *sheet*, and reify column name.'
        if self._cachedValues:
            self._cachedValues.clear()
        if sheet:
            self.sheet = sheet
        self.name = self._name

    @property
    def name(self):
        'Name of this column.'
        return self._name or ''

    @name.setter
    def name(self, name):
        if name is None:
            name = ''
        if isinstance(name, str):
            name = name.strip()
        else:
            name = str(name)

        if self.sheet:
            name = self.sheet.maybeClean(name)

        self._name = name

    @property
    def typestr(self):
        'Type of this column as string.'
        return self._type.__name__

    @typestr.setter
    def typestr(self, v):
        self.type = vd.getGlobals()[v or 'anytype']

    @property
    def type(self):
        'Type of this column.'
        return self._type

    @type.setter
    def type(self, t):
        if self._type != t:
            vd.addUndo(setattr, self, '_type', self.type)
        if not t:
            self._type = anytype
        elif isinstance(t, str):
            self.typestr = t
        else:
            self._type = t

    @property
    def width(self):
        'Width of this column in characters.  0 or negative means hidden.  None means not-yet-autocomputed.'
        return self._width

    @width.setter
    def width(self, w):
        if self.width != w:
            if self.width == 0 or w == 0:  # hide/unhide
                vd.addUndo(setattr, self, '_width', self.width)
            self._width = w

    @property
    def _formatdict(col):
        if '=' in col.fmtstr:
            return dict(val.split('=', maxsplit=1) for val in col.fmtstr.split())
        return {}

    @property
    def fmtstr(self):
        'Format string to use to display this column.'
        return self._fmtstr or vd.getType(self.type).fmtstr

    @fmtstr.setter
    def fmtstr(self, v):
        self._fmtstr = v

    def format_generic(self, fmtstr):
        return self.formatValue

    def format_json(self, fmtstr):
        return lambda v,*args,**kwargs: json.dumps(v)

    def format_python(self, fmtstr):
        return lambda v,*args,**kwargs: str(v)

    def format(self, *args, **kwargs):
        self._formatMaker = getattr(self, 'format_'+(self.formatter or self.sheet.options.disp_formatter))
        return self._formatMaker(self._formatdict)(*args, **kwargs)

    def formatValue(self, typedval, width=None):
        'Return displayable string of *typedval* according to ``Column.fmtstr``.'
        if typedval is None:
            return None

        if self.type is anytype:
            if isinstance(typedval, (dict, list, tuple)):
                dispval, dispw = clipstr(iterchars(typedval), width)
                return dispval

        if isinstance(typedval, bytes):
            typedval = typedval.decode(options.encoding, options.encoding_errors)

        return vd.getType(self.type).formatter(self.fmtstr, typedval)

    def hide(self, hide=True):
        if hide:
            self.setWidth(0)
        else:
            self.setWidth(abs(self.width or self.getMaxWidth(self.sheet.visibleRows)))

    @property
    def hidden(self):
        'Return True if width of this column is 0 or negative.'
        if self.width is None:
            return False
        return self.width <= 0

    def calcValue(self, row):
        'Calculate and return value for *row* in this column.'
        return (self.getter)(self, row)

    def getTypedValue(self, row):
        'Return the properly-typed value for the given row at this column, or a TypedWrapper object in case of null or error.'
        return wrapply(self.type, wrapply(self.getValue, row))

    def setCache(self, cache):
        '''Set cache behavior for this column to *cache*:

           - ``False`` (default): getValue never caches; calcValue is always called.
           - ``True``: getValue maintains a cache of ``options.col_cache_size``.
           - ``"async"``: ``getValue`` launches thread for every uncached result, maintains cache of infinite size.  Returns invalid value until cache entry available.'''
        self.cache = cache
        self._cachedValues = collections.OrderedDict() if self.cache else None

    @asyncthread
    def _calcIntoCacheAsync(self, row):
        # causes isues when moved into _calcIntoCache gen case
        self._cachedValues[self.sheet.rowid(row)] = INPROGRESS
        self._calcIntoCache(row)

    def _calcIntoCache(self, row):
        ret = wrapply(self.calcValue, row)
        if not isinstance(ret, TypedExceptionWrapper) or ret.val is not INPROGRESS:
            self._cachedValues[self.sheet.rowid(row)] = ret
        return ret

    def getValue(self, row):
        'Return value for *row* in this column, calculating if not cached.'

        if self.sheet.defer:
            try:
                row, rowmods = self.sheet._deferredMods[self.sheet.rowid(row)]
                return rowmods[self]
            except KeyError:
                pass

        if self._cachedValues is None:
            return self.calcValue(row)

        k = self.sheet.rowid(row)
        if k in self._cachedValues:
            return self._cachedValues[k]

        if self.cache == 'async':
            ret = self._calcIntoCacheAsync(row)
        else:
            ret = self._calcIntoCache(row)

            cachesize = options.col_cache_size
            if cachesize > 0 and len(self._cachedValues) > cachesize:
                self._cachedValues.popitem(last=False)

        return ret

    def getCell(self, row):
        'Return DisplayWrapper for displayable cell value.'
        cellval = wrapply(self.getValue, row)
        typedval = wrapply(self.type, cellval)

        if isinstance(typedval, TypedWrapper):
            if isinstance(cellval, TypedExceptionWrapper):  # calc failed
                exc = cellval.exception
                if cellval.forwarded:
                    dispval = str(cellval)  # traceback.format_exception_only(type(exc), exc)[-1].strip()
                else:
                    dispval = options.disp_error_val
                return DisplayWrapper(cellval.val, error=exc.stacktrace,
                                        display=dispval,
                                        note=options.note_getter_exc,
                                        notecolor='color_error')
            elif typedval.val is None:  # early out for strict None
                return DisplayWrapper(None, display='',  # force empty display for None
                                            note=options.disp_note_none,
                                            notecolor='color_note_type')
            elif isinstance(typedval, TypedExceptionWrapper):  # calc succeeded, type failed
                return DisplayWrapper(typedval.val, display=str(cellval),
                                            error=typedval.stacktrace,
                                            note=options.note_type_exc,
                                            notecolor='color_warning')
            else:
                return DisplayWrapper(typedval.val, display=str(typedval.val),
                                            error='unknown',
                                            note=options.note_type_exc,
                                            notecolor='color_warning')

        elif isinstance(typedval, threading.Thread):
            return DisplayWrapper(None,
                                display=options.disp_pending,
                                note=options.note_pending,
                                notecolor='color_note_pending')

        dw = DisplayWrapper(cellval)

        try:
            dw.display = self.format(typedval, width=self.width*2) or ''

            # annotate cells with raw value type in anytype columns, except for strings
            if self.type is anytype and type(cellval) is not str:
                typedesc = vd.typemap.get(type(cellval), None)
                if typedesc:
                    dw.note = typedesc.icon
                    dw.notecolor = 'color_note_type'

        except Exception as e:  # formatting failure
            e.stacktrace = stacktrace()
            dw.error = e.stacktrace
            try:
                dw.display = str(cellval)
            except Exception as e:
                dw.display = str(e)
            dw.note = options.note_format_exc
            dw.notecolor = 'color_warning'

        return dw

    def getDisplayValue(self, row):
        'Return string displayed in this column for given *row*.'
        return self.getCell(row).display

    def putValue(self, row, val):
        'Change value for *row* in this column to *val* immediately.  Does not check the type.  Overrideable; by default calls ``.setter(row, val)``.'
        return self.setter(self, row, val)

    def setValue(self, row, val):
        'Change value for *row* in this column to *val*.  Call ``putValue`` immediately if parent ``sheet.defer`` is False, otherwise cache until later ``putChanges``.  Caller must add undo function.'
        if self.sheet.defer:
            self.cellChanged(row, val)
        else:
            self.putValue(row, val)
        self.sheet.setModified()

    def setValueSafe(self, row, value):
        'setValue and ignore exceptions.'
        try:
            return self.setValue(row, value)
        except Exception as e:
            vd.exceptionCaught(e)

    @asyncthread
    def setValues(self, rows, *values):
        'Set values in this column for *rows* to *values*, recycling values as needed to fill *rows*.'
        vd.addUndoSetValues([self], rows)
        for r, v in zip(rows, itertools.cycle(values)):
            self.setValueSafe(r, v)
        self.recalc()
        return vd.status('set %d cells to %d values' % (len(rows), len(values)))

    def setValuesTyped(self, rows, *values):
        'Set values on this column for *rows* to *values*, coerced to column type, recycling values as needed to fill *rows*.  Abort on type exception.'
        vd.addUndoSetValues([self], rows)
        for r, v in zip(rows, itertools.cycle(self.type(val) for val in values)):
            self.setValueSafe(r, v)

        self.recalc()

        return vd.status('set %d cells to %d values' % (len(rows), len(values)))

    def getMaxWidth(self, rows):
        'Return the maximum length of any cell in column or its header (up to window width).'
        w = 0
        nlen = dispwidth(self.name)
        if len(rows) > 0:
            w = max(max(dispwidth(self.getDisplayValue(r), maxwidth=self.sheet.windowWidth) for r in rows), nlen)+2
        return max(w, nlen)


# ---- Column makers

def setitem(r, i, v):  # function needed for use in lambda
    r[i] = v
    return True


def getattrdeep(obj, attr, *default, getter=getattr):
    try:
        'Return dotted attr (like "a.b.c") from obj, or default if any of the components are missing.'
        if not isinstance(attr, str):
            return getter(obj, attr, *default)

        try:  # if attribute exists, return toplevel value, even if dotted
            if attr in obj:
                return getter(obj, attr)
        except Exception as e:
            pass

        attrs = attr.split('.')
        for a in attrs[:-1]:
            obj = getter(obj, a)

        return getter(obj, attrs[-1])
    except Exception as e:
        if not default: raise
        return default[0]


def setattrdeep(obj, attr, val, getter=getattr, setter=setattr):
    'Set dotted attr (like "a.b.c") on obj to val.'
    if not isinstance(attr, str):
        return setter(obj, attr, val)

    try:  # if attribute exists, overwrite toplevel value, even if dotted
        getter(obj, attr)
        return setter(obj, attr, val)
    except Exception as e:
        pass

    attrs = attr.split('.')
    for a in attrs[:-1]:
        try:
            obj = getter(obj, a)
        except Exception as e:
            obj = obj[a] = type(obj)()  # assume homogenous nesting

    setter(obj, attrs[-1], val)


def getitemdeep(obj, k, *default):
    return getattrdeep(obj, k, *default, getter=getitem)

def setitemdeep(obj, k, val):
    return setattrdeep(obj, k, val, getter=getitemdef, setter=setitem)

def AttrColumn(name='', attr=None, **kwargs):
    'Column using getattr/setattr with *attr*.'
    return Column(name,
                  expr=attr if attr is not None else name,
                  getter=lambda col,row: getattrdeep(row, col.expr),
                  setter=lambda col,row,val: setattrdeep(row, col.expr, val),
                  **kwargs)

def getitem(o, k, default=None):
    return default if o is None else o[k]

def getitemdef(o, k, default=None):
    try:
        return default if o is None else o[k]
    except Exception:
        return default

class ItemColumn(Column):
    'Column using getitem/setitem with *key*.'
    def __init__(self, name=None, expr=None, **kwargs):
        super().__init__(name,
            expr=expr if expr is not None else name,
            getter=lambda col,row: getitemdeep(row, col.expr, None),
            setter=lambda col,row,val: setitemdeep(row, col.expr, val),
            **kwargs)


class SubColumnFunc(Column):
    'Column compositor; preprocess row with *subfunc*(row, *expr*) before passing to *origcol*.getValue and *origcol*.setValue.'
    def __init__(self, name='', origcol=None, expr=None, subfunc=getitemdef, **kwargs):
        super().__init__(name, type=origcol.type, width=origcol.width, expr=expr, **kwargs)
        self.origcol = origcol
        self.subfunc = subfunc

    def calcValue(self, row):
        subrow = self.subfunc(row, self.expr)
        if subrow is not None:
            # call getValue to use deferred values from source sheet
            return self.origcol.getValue(subrow)

    def putValue(self, row, value):
        subrow = self.subfunc(row, self.expr)
        if subrow is None:
            vd.fail('no source row')
        self.origcol.setValue(subrow, value)

    def recalc(self, sheet=None):
        Column.recalc(self, sheet)
        self.origcol.recalc()  # reset cache but don't change sheet


def SubColumnAttr(attrname, c, **kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = c.name
    return SubColumnFunc(origcol=c, subfunc=getattrdeep, expr=attrname, **kwargs)

def SubColumnItem(idx, c, **kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = c.name
    return SubColumnFunc(origcol=c, subfunc=getitemdef, expr=idx, **kwargs)

class ExprColumn(Column):
    'Column using *expr* to derive the value from each row.'
    def __init__(self, name, expr=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = expr or name
        self.ncalcs = 0
        self.totaltime = 0
        self.maxtime = 0

    def calcValue(self, row):
        t0 = time.perf_counter()
        r = self.sheet.evalExpr(self.compiledExpr, row, col=self)
        t1 = time.perf_counter()
        self.ncalcs += 1
        self.maxtime = max(self.maxtime, t1-t0)
        self.totaltime += (t1-t0)
        return r

    def putValue(self, row, val):
        a = self.getDisplayValue(row)
        b = self.format(self.type(val))
        if a != b:
            vd.warning('%s calced %s not %s' % (self.name, a, b))

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr):
        self.compiledExpr = compile(expr, '<expr>', 'eval') if expr else None
        self._expr = expr


class SettableColumn(Column):
    'Column using rowid to store and retrieve values internally.'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store = {}

    def putValue(self, row, value):
        self._store[self.sheet.rowid(row)] = value

    def calcValue(self, row):
        return self._store.get(self.sheet.rowid(row), None)


# synonyms
ColumnItem = ItemColumn
ColumnAttr = AttrColumn
ColumnExpr = ExprColumn
