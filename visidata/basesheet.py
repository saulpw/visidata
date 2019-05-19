import visidata
from visidata import Extensible, getGlobals, vd, EscapeException, catchapply
from unittest import mock


class LazyMap:
    'provides a lazy mapping to obj attributes.  useful when some attributes are expensive properties.'
    def __init__(self, *objs):
        self.locals = {}
        self.objs = {} # [k] -> obj
        for obj in objs:
            for k in dir(obj):
                if k not in self.objs:
                    self.objs[k] = obj

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


class BaseSheet(Extensible):
    _rowtype = object    # callable (no parms) that returns new empty item
    _coltype = None      # callable (no parms) that returns new settable view into that item
    rowtype = 'objects'  # one word, plural, describing the items
    precious = True      # False for a few discardable metasheets

    def __init__(self, name, **kwargs):
        self.name = name
        self.source = None
        self.shortcut = ''
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode

        self.__dict__.update(kwargs)

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        else:
            return id(self) < id(other)

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.precious = True  # copies can be precious even if originals aren't
        return ret

    def __bool__(self):
        'an instantiated Sheet always tests true'
        return True

    def __len__(self):
        return 0

    def __contains__(self, vs):
        if self.source is vs:
            return True
        if isinstance(self.source, BaseSheet):
            return vs in self.source
        return False

    @property
    def loaded(self):
        return False

    @property
    def windowHeight(self):
        'Height of the current sheet, in terminal lines'
        return self._scr.getmaxyx()[0] if self._scr else 25

    @property
    def windowWidth(self):
        'Width of the current sheet, in single-width characters'
        return self._scr.getmaxyx()[1] if self._scr else 80

    def exec_keystrokes(self, keystrokes, vdglobals=None):
        return self.exec_command(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

    def exec_command(self, cmd, args='', vdglobals=None, keystrokes=None):
        "Execute `cmd` tuple with `vdglobals` as globals and this sheet's attributes as locals.  Returns True if user cancelled."
        if not cmd:
            vd.debug('no command "%s"' % keystrokes)
            return True

        escaped = False
        err = ''

        if vdglobals is None:
            vdglobals = getGlobals()

        self.sheet = self

        try:
            if vd.cmdlog:
                vd.cmdlog.beforeExecHook(self, cmd, '', keystrokes)
            code = compile(cmd.execstr, cmd.longname, 'exec')
            vd.debug(cmd.longname)
            exec(code, vdglobals, LazyMap(vd, self))
        except EscapeException as e:  # user aborted
            vd.warning('aborted')
            escaped = True
        except Exception as e:
            vd.debug(cmd.execstr)
            err = vd.exceptionCaught(e)
            escaped = True

        try:
            if vd.cmdlog:
                # sheet may have changed
                vd.cmdlog.afterExecSheet(vd.sheets[0] if vd.sheets else None, escaped, err)
        except Exception as e:
            vd.exceptionCaught(e)

        catchapply(self.checkCursor)

        vd.clear_caches()
        return escaped

    @property
    def name(self):
        return self._name or ''

    @name.setter
    def name(self, name):
        'Set name without spaces.'
        self._name = name.strip().replace(' ', '_')

    def recalc(self):
        'Clear any calculated value caches.'
        pass

    def draw(self, scr):
        vd.error('no draw')

    def refresh(self):
        self._scr.clear()
        self._scr.refresh()

    def reload(self):
        vd.error('no reload')

    def checkCursor(self):
        pass

    def newRow(self):
        return type(self)._rowtype()
