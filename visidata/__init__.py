'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '3.1.1'
__version_info__ = 'VisiData v' + __version__
__author__ = 'Saul Pwanson <vd@saul.pw>'
__status__ = 'Production/Stable'
__copyright__ = 'Copyright (c) 2016-2021 ' + __author__


class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass


def addGlobals(*args, **kwargs):
    '''Update the VisiData globals dict with items from *args* and *kwargs*; to add symbols available to command execstrings and eval strings like command expr.'

    Dunder methods are ignored, to prevent accidentally overwriting housekeeping methods.'''
    drop_dunder = lambda d: {k: v for k, v in d.items() if not k.startswith("__")}
    for g in args:
        globals().update(drop_dunder(g))
    globals().update(drop_dunder(kwargs))


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

# importModule tracks where commands/options/etc are coming from (via vd.importingModule)
core_imports = '''
import visidata.errors
import visidata.editor
import visidata.color
import visidata.cliptext
import visidata.mainloop

import visidata.menu
import visidata.wrappers
import visidata.undo
import visidata._types
import visidata.column

import visidata.interface
import visidata.sheets
import visidata.rename_col
import visidata.indexsheet

import visidata.statusbar

import visidata.textsheet
import visidata.threads
import visidata.path
import visidata.guide

import visidata.stored_list
import visidata._input
import visidata.tuiwin
import visidata.mouse
import visidata.movement

import visidata.type_date

import visidata._urlcache
import visidata.selection
import visidata.text_source
import visidata.loaders
import visidata.loaders.tsv
import visidata.pyobj
import visidata.loaders.json
import visidata._open
import visidata.save
import visidata.search

import visidata.expr
import visidata.metasheets
import visidata.input_history
import visidata.optionssheet
import visidata.type_currency
import visidata.type_floatsi
import visidata.clean_names
import visidata.cmdlog
import visidata.clipboard
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
import visidata.windows

import visidata.form
import visidata.sidebar

import visidata.ddwplay
import visidata.plugins

import visidata.theme
import visidata.apps
import visidata.fuzzymatch
import visidata.hint
'''

for line in core_imports.splitlines():
    if not line: continue
    module = line[len('import '):]
    vd.importModule(module)

vd.importSubmodules('visidata.loaders')

def importFeatures():
    vd.importSubmodules('visidata.features')
    vd.importSubmodules('visidata.themes')

    import visidata.deprecated

    vd.importModule('copy', 'copy deepcopy'.split())
    vd.importModule('builtins', 'abs all any ascii bin bool bytes callable chr complex dict dir divmod enumerate eval filter float format getattr hex int len list map max min next oct ord pow range repr reversed round set sorted str sum tuple type zip'.split())
    vd.importModule('math', 'acos acosh asin asinh atan atan2 atanh ceil copysign cos cosh degrees dist erf erfc exp expm1 fabs factorial floor fmod frexp fsum gamma gcd hypot isclose isfinite isinf isnan isqrt lcm ldexp lgamma log log1p log10 log2 modf radians remainder sin sinh sqrt tan tanh trunc prod perm comb nextafter ulp pi e tau inf nan'.split())
    vd.importModule('random', 'randrange randint choice choices sample uniform gauss lognormvariate'.split())
    vd.importModule('string', 'ascii_letters ascii_lowercase ascii_uppercase digits hexdigits punctuation printable whitespace'.split())
    vd.importModule('json')
    vd.importModule('itertools')
    vd.importModule('curses')

    import visidata.experimental  # import nothing by default but make package accessible

vd.finalInit()  # call all VisiData.init() from modules

importFeatures()

vd.addGlobals(vd=vd) # globals())
