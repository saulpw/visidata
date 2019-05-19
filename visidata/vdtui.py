# Copyright 2017-2019 Saul Pwanson  http://visidata.org

'vdtui: a curses framework for columnar data'

from builtins import *
from unittest import mock
import sys
import os
import collections
from copy import copy, deepcopy
import curses
import datetime
from functools import wraps
import io
import itertools
import locale
import string
import re
import textwrap
import threading
import traceback
import time
import inspect
import weakref

class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass

class ExpectedException(Exception):
    'an expected exception'
    pass


vd = None  # will be filled in later



# undoers
def undoAttr(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value as reference.'
    return '''lambda oldvals=[(o, getattr(o, "{attrname}")) for o in {objs}] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoAttrCopy(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value which is copied.'
    return '''lambda oldvals=[ (o, copy(getattr(o, "{attrname}"))) for o in {objs} ] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoSetValues(rowstr='[cursorRow]', colstr='[cursorCol]'):
    return 'lambda oldvals=[(c, r, c.getValue(r)) for c,r in itertools.product({colstr}, {rowstr})]: list(c.setValue(r, v) for c, r, v in oldvals)'.format(rowstr=rowstr, colstr=colstr)

def undoRows(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, 'rows')

undoBlocked = 'lambda: error("cannot undo")'
undoSheetRows = undoRows('sheet')
undoSheetCols = 'lambda sheet=sheet,oldcols=[copy(c) for c in columns]: setattr(sheet, "columns", oldcols)'
undoAddCols = undoAttrCopy('[sheet]', 'columns')
undoEditCell = undoSetValues('[cursorRow]', '[cursorCol]')
undoEditCells = undoSetValues('selectedRows', '[cursorCol]')


ENTER='^J'
ALT=ESC='^['
###

def stacktrace(e=None):
    if not e:
        return traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)

# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @wraps(func)
    def _execAsync(*args, **kwargs):
        return vd.execAsync(func, *args, **kwargs)
    return _execAsync


class Extensible:
    @classmethod
    def init(cls, membername, initfunc, **kwargs):
        'Add `self.attr=T()` to cls.__init__.  Usage: cls.init("attr", T[, copy=True])'
        oldinit = cls.__init__
        def newinit(self, *args, **kwargs):
            oldinit(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.__init__ = newinit

        oldcopy = cls.__copy__
        def newcopy(self, *args, **kwargs):
            ret = oldcopy(self, *args, **kwargs)
            setattr(ret, membername, getattr(self, membername) if kwargs.get('copy', False) else initfunc())
            return ret
        cls.__copy__ = newcopy

    @classmethod
    def api(cls, func):
        oldfunc = getattr(cls, func.__name__, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, func.__name__, func)
        return func

    @classmethod
    def class_api(cls, func):
        name = func.__get__(None, dict).__func__.__name__
        oldfunc = getattr(cls, name, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, name, func)
        return func

    @classmethod
    def property(cls, func):
        @property
        def dofunc(self):
            return func(self)
        setattr(cls, func.__name__, dofunc)
        return dofunc

    @classmethod
    def cached_property(cls, func):
        @property
        @wraps(func)
        def get_if_not(self):
            name = '_' + func.__name__
            if not hasattr(self, name):
                setattr(self, name, func(self))
            return getattr(self, name)
        setattr(cls, func.__name__, get_if_not)
        return get_if_not


class VisiData(Extensible):
    allPrefixes = ['g', 'z', ESC]  # embig'g'en, 'z'mallify, ESC=Alt/Meta

    @classmethod
    def global_api(cls, func):
        'Make global func() and identical vd.func()'
        def _vdfunc(*args, **kwargs):
            return func(vd, *args, **kwargs)
        setattr(cls, func.__name__, func)
        return wraps(func)(_vdfunc)

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = []  # list of all non-precious sheets ever pushed
        self.lastErrors = []
        self.keystrokes = ''
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode
        self.mousereg = []
        self.cmdlog = None

    def __copy__(self):
        'Dummy method for Extensible.init()'
        pass

    def finalInit(self):
        'Initialize members specified in other modules with init()'
        pass

    @classmethod
    def init(cls, membername, initfunc, **kwargs):
        'Overload Extensible.init() to call finalInit instead of __init__'
        oldinit = cls.finalInit
        def newinit(self, *args, **kwargs):
            oldinit(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.finalInit = newinit
        super().init(membername, lambda: None, **kwargs)

    def quit(self):
        if len(vd.sheets) == 1 and options.quitguard:
            confirm("quit last sheet? ")
        return vd.sheets.pop(0)

    @property
    def sheet(self):
        'the top sheet on the stack'
        return self.sheets[0] if self.sheets else None

    def getSheet(self, sheetname):
        matchingSheets = [x for x in vd.sheets if x.name == sheetname]
        if matchingSheets:
            if len(matchingSheets) > 1:
                status('more than one sheet named "%s"' % sheetname)
            return matchingSheets[0]
        if sheetname == 'options':
            vs = self.optionsSheet
            vs.reload()
            vs.vd = vd
            return vs

    def clear_caches(self):
        'Invalidate internal caches between command inputs.'
        Sheet.visibleCols.fget.cache_clear()
        Sheet.keyCols.fget.cache_clear()
        Sheet.nHeaderRows.fget.cache_clear()
        Sheet.colsByName.fget.cache_clear()
        colors.colorcache.clear()
        self.mousereg.clear()

    def getkeystroke(self, scr, vs=None):
        'Get keystroke and display it on status bar.'
        k = None
        try:
            scr.refresh()
            k = scr.get_wch()
            self.drawRightStatus(scr, vs or self.sheets[0]) # continue to display progress %
        except curses.error:
            return ''  # curses timeout

        if isinstance(k, str):
            if ord(k) >= 32 and ord(k) != 127:  # 127 == DEL or ^?
                return k
            k = ord(k)
        return curses.keyname(k).decode('utf-8')

    def onMouse(self, scr, y, x, h, w, **kwargs):
        self.mousereg.append((scr, y, x, h, w, kwargs))

    def getMouse(self, _scr, _x, _y, button):
        for scr, y, x, h, w, kwargs in self.mousereg[::-1]:
            if scr == _scr and x <= _x < x+w and y <= _y < y+h and button in kwargs:
                return kwargs[button]

    @property
    def windowHeight(self):
        return self._scr.getmaxyx()[0] if self._scr else 25

    @property
    def windowWidth(self):
        return self._scr.getmaxyx()[1] if self._scr else 80
# end VisiData class

vd = VisiData()

### external interface
def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)

def getGlobals():
    return globals()

