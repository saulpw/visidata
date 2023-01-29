'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '2.12dev'
__version_info__ = 'VisiData v' + __version__
__author__ = 'Saul Pwanson <vd@saul.pw>'
__status__ = 'Production/Stable'
__copyright__ = 'Copyright (c) 2016-2021 ' + __author__


class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass


def addGlobals(*args, **kwargs):
    '''Update the VisiData globals dict with items from *args* and *kwargs*, which are mappings of names to functions.
    Importers can call ``addGlobals(globals())`` to have their globals accessible to execstrings.'''
    for g in args:
        globals().update(g)
    globals().update(kwargs)


def getGlobals():
    'Return the VisiData globals dict.'
    return globals()

from .utils import *

from .extensible import *
from .vdobj import *
vd = VisiData()

vd.version = __version__

vd.addGlobals = addGlobals
vd.getGlobals = getGlobals

import visidata.keys

from .basesheet import *

import visidata.settings

for line in '''
import visidata.errors
import visidata.editor
import visidata.cliptext
import visidata.color
import visidata.mainloop

import visidata.wrappers
import visidata.undo
import visidata._types
import visidata.column

import visidata.interface
import visidata.sheets

import visidata.statusbar

import visidata.textsheet
import visidata.threads
import visidata.path

import visidata._input
import visidata.movement

import visidata.type_currency
import visidata.type_date
import visidata.type_floatsi

import visidata._urlcache
import visidata.selection
import visidata.loaders
import visidata.loaders.tsv
import visidata.pyobj
import visidata.loaders.json
import visidata._open
import visidata.metasheets
import visidata.cmdlog
import visidata.save
import visidata.clipboard
import visidata.search
import visidata.expr

import visidata.menu
import visidata.choose
import visidata.aggregators
import visidata.pivot
import visidata.freqtbl
import visidata.canvas
import visidata.canvas_text
import visidata.graph
import visidata.motd
import visidata.shell
import visidata.main
import visidata.help
import visidata.modify
import visidata.sort
import visidata.memory
import visidata.macros
import visidata.macos

import visidata.form

import visidata.ddwplay
import visidata.plugins

import visidata.theme
'''.splitlines():
    if not line: continue
    assert line.startswith('import visidata.'), line
    module = line[len('import visidata.'):]
    vd.importModule('visidata.' + module)

vd.importSubmodules('visidata.features')
vd.importSubmodules('visidata.themes')

vd.importSubmodules('visidata.loaders')

vd.importStar('visidata.deprecated')

vd.importStar('builtins')
vd.importStar('copy')
vd.importStar('math')
vd.importStar('random')


vd.finalInit()  # call all VisiData.init() from modules

vd.addGlobals(globals())
