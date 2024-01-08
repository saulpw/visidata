import os

import visidata
from visidata import Extensible, VisiData, vd, EscapeException, MissingAttrFormatter, AttrDict


UNLOADED = tuple()  # sentinel for a sheet not yet loaded for the first time

vd.beforeExecHooks = [] # func(sheet, cmd, args, keystrokes) called before the exec()

class LazyChainMap:
    'provides a lazy mapping to obj attributes.  useful when some attributes are expensive properties.'
    def __init__(self, *objs, locals=None):
        self.locals = {} if locals is None else locals
        self.objs = {} # [k] -> obj
        for obj in objs:
            for k in dir(obj):
                if k not in self.objs:
                    self.objs[k] = obj

    def __iter__(self):
        return iter(self.objs)

    def __contains__(self, k):
        return k in self.objs

    def keys(self):
        return list(self.objs.keys())  # sum(set(dir(obj)) for obj in self.objs))

    def get(self, key, default=None):
        if key in self.locals:
            return self.locals[key]
        return self.objs.get(key, default)

    def clear(self):
        self.locals.clear()

    def __getitem__(self, k):
        obj = self.objs.get(k, None)
        if obj:
            return getattr(obj, k)
        return self.locals[k]

    def __setitem__(self, k, v):
        obj = self.objs.get(k, None)
        if obj:
            return setattr(obj, k, v)
        self.locals[k] = v


class DrawablePane(Extensible):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    'Base class for all interaction owners that can be drawn in a window.'
    def draw(self, scr):
        'Draw on the terminal window *scr*.  Should be overridden.'
        vd.error('no draw')

    @property
    def windowHeight(self):
        'Height of the current sheet window, in terminal lines.'
        return self._scr.getmaxyx()[0] if self._scr else 25

    @property
    def windowWidth(self):
        'Width of the current sheet window, in single-width characters.'
        return self._scr.getmaxyx()[1] if self._scr else 80

    def execCommand2(self, cmd, vdglobals=None):
        "Execute `cmd` with `vdglobals` as globals and this sheet's attributes as locals.  Return True if user cancelled."

        try:
            self.sheet = self
            code = compile(cmd.execstr, cmd.longname, 'exec')
            exec(code, vdglobals, LazyChainMap(vd, self))
            return False
        except EscapeException as e:  # user aborted
            vd.warning(str(e))
            return True


class _dualproperty:
    'Return *obj_method* or *cls_method* depending on whether property is on instance or class.'
    def __init__(self, obj_method, cls_method):
        self._obj_method = obj_method
        self._cls_method = cls_method

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self._cls_method(objtype)
        else:
            return self._obj_method(obj)


class BaseSheet(DrawablePane):
    'Base class for all sheet types.'
    _rowtype = object    # callable (no parms) that returns new empty item
    _coltype = None      # callable (no parms) that returns new settable view into that item
    rowtype = 'objects'  # one word, plural, describing the items
    precious = True      # False for a few discardable metasheets
    defer = False        # False for not deferring changes until save
    guide = ''           # default to show in sidebar

    def _obj_options(self):
        return vd.OptionsObject(vd._options, obj=self)

    def _class_options(cls):
        return vd.OptionsObject(vd._options, obj=cls)

    class_options = options = _dualproperty(_obj_options, _class_options)

    def __init__(self, *names, rows=UNLOADED, **kwargs):
        self._name = None   # initial cache value necessary for self.options
        self.loading = False
        self.names = list(names)
        self.name = self.options.name_joiner.join(str(x) for x in self.names if x)
        self.source = None
        self.rows = rows      # list of opaque objects
        self._scr = None
        self.hasBeenModified = False

        super().__init__(**kwargs)

        self._sidebar = ''

    def setModified(self):
        if not self.hasBeenModified:
            vd.addUndo(setattr, self, 'hasBeenModified', self.hasBeenModified)
            self.hasBeenModified = True

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        else:
            return id(self) < id(other)

    def __copy__(self):
        'Return shallow copy of sheet.'
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.precious = True  # copy can be precious even if original is not
        ret.hasBeenModified = False  # copy is not modified even if original is
        return ret

    def __bool__(self):
        'an instantiated Sheet always tests true'
        return True

    def __len__(self):
        'Number of elements on this sheet.'
        return self.nRows

    def __str__(self):
        return self.name

    @property
    def rows(self):
        return self._rows

    @rows.setter
    def rows(self, rows):
        self._rows = rows

    @property
    def nRows(self):
        'Number of rows on this sheet.  Override in subclass.'
        return 0

    def __contains__(self, vs):
        if self.source is vs:
            return True
        if isinstance(self.source, BaseSheet):
            return vs in self.source
        return False

    @property
    def displaySource(self):
        if isinstance(self.source, BaseSheet):
            return f'the *{self.source}* sheet'

        if isinstance(self.source, (list, tuple)):
            if len(self.source) == 1:
                return f'the **{self.source[0]}** sheet'
            return f'{len(self.source)} sheets'

        return f'**{self.source}**'

    def execCommand(self, longname, vdglobals=None, keystrokes=None):
        if ' ' in longname:
            cmd, arg = longname.split(' ', maxsplit=1)
            vd.injectInput(arg)

        cmd = self.getCommand(longname or keystrokes)
        if not cmd:
            vd.warning('no command for %s' % (longname or keystrokes))
            return False

        escaped = False
        err = ''

        if vdglobals is None:
            vdglobals = vd.getGlobals()

        vd.cmdlog  # make sure cmdlog has been created for first command

        try:
            for hookfunc in vd.beforeExecHooks:
                hookfunc(self, cmd, '', keystrokes)
            escaped = super().execCommand2(cmd, vdglobals=vdglobals)
        except Exception as e:
            vd.debug(cmd.execstr)
            err = vd.exceptionCaught(e)
            escaped = True

        if vd.cmdlog:
            # sheet may have changed
            vd.callNoExceptions(vd.cmdlog.afterExecSheet, vd.activeSheet, escaped, err)

        vd.callNoExceptions(self.checkCursor)

        vd.clearCaches()

        for t in self.currentThreads:
            if not hasattr(t, 'lastCommand'):
                t.lastCommand = True

        return escaped

    @property
    def lastCommandThreads(self):
        return [t for t in self.currentThreads if getattr(t, 'lastCommand', None)]

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, names):
        self._names = names
        self.name = self.options.name_joiner.join(self.maybeClean(str(x)) for x in self._names)

    @property
    def name(self):
        'Name of this sheet.'
        return self._name

    @name.setter
    def name(self, name):
        'Set name without spaces.'
        if self._names:
            vd.addUndo(setattr, self, '_names', self._names)
        self._name = self.maybeClean(str(name))

    def maybeClean(self, s):
        'stub'
        return s

    def recalc(self):
        'Clear any calculated value caches.'
        pass

    def refresh(self):
        'Recalculate any internal state needed for `draw()`.  Overridable.'
        pass

    def ensureLoaded(self):
        'Call ``reload()`` if not already loaded.'
        if self.rows is UNLOADED:
            self.rows = []  # prevent auto-reload from running twice
            return self.reload()   # likely launches new thread

    def reload(self):
        'Load sheet from *self.source*.  Override in subclass.'
        vd.error('no reload')

    @property
    def cursorRow(self):
        'The row object at the row cursor.  Overridable.'
        return None

    def checkCursor(self):
        'Check cursor and fix if out-of-bounds.  Overridable.'
        pass

    def evalExpr(self, expr, **kwargs):
        'Evaluate Python expression *expr* in the context of *kwargs* (may vary by sheet type).'
        return eval(expr, vd.getGlobals(), dict(sheet=self))

    def formatString(self, fmt, **kwargs):
        'Return formatted string with *sheet* and *vd* accessible to expressions.  Missing expressions return empty strings instead of error.'
        return MissingAttrFormatter().format(fmt, sheet=self, vd=vd, **kwargs)



@VisiData.api
def redraw(vd):
    'Clear the terminal screen and let the next draw cycle recreate the windows and redraw everything.'
    for vs in vd.sheets:
        vs._scr = None
    if vd.win1: vd.win1.clear()
    if vd.win2: vd.win2.clear()
    if vd.scrFull:
        vd.scrFull.clear()
        vd.setWindows(vd.scrFull)


@VisiData.property
def sheet(self):
    return self.activeSheet

@VisiData.api
def isLongname(self, ks:str):
    'Return True if *ks* is a longname.'
    return ('-' in ks) and (ks[-1] != '-') or (len(ks) > 3 and ks.islower())


@VisiData.api
def getSheet(vd, sheetname):
    'Return Sheet from the sheet stack.  *sheetname* can be a sheet name or a sheet number indexing directly into ``vd.sheets``.'
    if isinstance(sheetname, BaseSheet):
        return sheetname
    matchingSheets = [x for x in vd.sheets if x.name == sheetname]
    if matchingSheets:
        if len(matchingSheets) > 1:
            vd.warning('more than one sheet named "%s"' % sheetname)
        return matchingSheets[0]

    try:
        sheetidx = int(sheetname)
        return vd.sheets[sheetidx]
    except ValueError:
        pass

    if sheetname == 'options':
        vs = vd.globalOptionsSheet
        vs.reload()
        vs.vd = vd
        return vs
