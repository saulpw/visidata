import os

import visidata
from visidata import Extensible, VisiData, vd, EscapeException, cleanName
from unittest import mock


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

    def __contains__(self, k):
        return k in self.objs

    def keys(self):
        return list(self.objs.keys())  # sum(set(dir(obj)) for obj in self.objs))

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

    def _obj_options(self):
        return vd.OptionsObject(vd._options, obj=self)

    def _class_options(cls):
        return vd.OptionsObject(vd._options, obj=cls)

    class_options = options = _dualproperty(_obj_options, _class_options)

    def __init__(self, *names, **kwargs):
        self._name = None   # initial cache value necessary for self.options
        self.names = names
        self.name = self.options.name_joiner.join(str(x) for x in self.names if x)
        self.source = None
        self.rows = UNLOADED      # list of opaque objects
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode
        self.mouseX = 0
        self.mouseY = 0
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
    def nRows(self):
        'Number of rows on this sheet.  Override in subclass.'
        return 0

    def __contains__(self, vs):
        if self.source is vs:
            return True
        if isinstance(self.source, BaseSheet):
            return vs in self.source
        return False

    def execCommand(self, cmd, vdglobals=None, keystrokes=None):
        cmd = self.getCommand(cmd or keystrokes)
        if not cmd:
            if keystrokes:
                vd.status('no command for %s' % keystrokes)
            return False

        escaped = False
        err = ''

        if vdglobals is None:
            vdglobals = vd.getGlobals()

        vd.cmdlog  # make sure cmdlog has been created for first command

        try:
            for hookfunc in vd.beforeExecHooks:
                hookfunc(self, cmd, '', keystrokes)
            vd.debug(cmd.longname)
            escaped = super().execCommand2(cmd, vdglobals=vdglobals)
        except Exception as e:
            vd.debug(cmd.execstr)
            err = vd.exceptionCaught(e)
            escaped = True

        try:
            if vd.cmdlog:
                # sheet may have changed
                vd.cmdlog.afterExecSheet(vd.activeSheet, escaped, err)
        except Exception as e:
            vd.exceptionCaught(e)

        self.checkCursorNoExceptions()

        vd.clearCaches()
        return escaped

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
        if self.options.clean_names:
            s = cleanName(s)
        return s

    def recalc(self):
        'Clear any calculated value caches.'
        pass

    def refresh(self):
        'Clear the terminal screen and let the next draw cycle redraw everything.'
        if self._scr:
            self._scr.clear()
            self._scr.refresh()

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
        'The row object at the row cursor.  Overrideable.'
        return None

    def checkCursor(self):
        'Check cursor and fix if out-of-bounds.  Overrideable.'
        pass

    def checkCursorNoExceptions(self):
        try:
            return self.checkCursor()
        except Exception as e:
            vd.exceptionCaught(e)

    def evalExpr(self, expr, **kwargs):
        'Evaluate Python expression *expr* in the context of *kwargs* (may vary by sheet type).'
        return eval(expr, vd.getGlobals(), None)

    @property
    def sidebar(self):
        'Default implementation just returns set value.  Overrideable.'
        return self._sidebar

    @sidebar.setter
    def sidebar(self, v):
        'Default implementation just sets value.  Overrideable.'
        self._sidebar = v

    @property
    def sidebar_title(self):
        'Default implementation returns fixed value.  Overrideable.'
        return 'sidebar'


@VisiData.api
def redraw(vd):
    'Clear the terminal screen and let the next draw cycle recreate the windows and redraw everything.'
    for vs in vd.sheets:
        vs._scr = None
    vd.scrFull.clear()
    vd.win1.clear()
    vd.win2.clear()
    vd.setWindows(vd.scrFull)


@VisiData.property
def sheet(self):
    return self.activeSheet

@VisiData.api
def isLongname(self, ks):
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
