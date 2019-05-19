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

vd = None  # will be filled in later

###

# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @wraps(func)
    def _execAsync(*args, **kwargs):
        return vd.execAsync(func, *args, **kwargs)
    return _execAsync

from visidata import VisiData


vd = VisiData()

### external interface
def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)

def getGlobals():
    return globals()

