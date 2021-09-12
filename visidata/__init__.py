'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '2.6dev'
__version_info__ = 'VisiData v' + __version__
__author__ = 'Saul Pwanson <vd@saul.pw>'
__status__ = 'Production/Stable'
__copyright__ = 'Copyright (c) 2016-2021 ' + __author__


class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass


def addGlobals(g):
    '''Update the VisiData globals dict with items from *g*, which is a mapping of names to functions.
    Importers can call ``addGlobals(globals())`` to have their globals accessible to execstrings.'''
    globals().update(g)


def getGlobals():
    'Return the VisiData globals dict.'
    return globals()

from builtins import *
from copy import copy, deepcopy

from .utils import *

from .extensible import *
from .vdobj import *
vd = VisiData()

vd.version = __version__

vd.addGlobals = addGlobals
vd.getGlobals = getGlobals

import visidata.keys

from .basesheet import *
from .settings import *
from .errors import *
from .editor import *
from .cliptext import *
from .color import *
from .mainloop import *
from .wrappers import *
from .undo import *

from ._types import *
from .column import *

theme = option  # convert theme(...) to option(...) and move this down, eventually into deprecated.py

from .sheets import *
from .statusbar import *

from .textsheet import *
from .threads import *
from ._input import *
import visidata.movement
from .path import *
from .urlcache import *
from .selection import *
from .loaders.tsv import *
from .pyobj import *
import visidata.loaders.json
import visidata._open
import visidata.save
import visidata.clipboard
import visidata.slide
import visidata.search
import visidata.expr

import visidata.menu
import visidata.choose
import visidata.metasheets
import visidata.join
import visidata.aggregators
import visidata.describe
import visidata.pivot
import visidata.freqtbl
import visidata.melt
import visidata.cmdlog
import visidata.freeze
import visidata.regex
import visidata.canvas
import visidata.canvas_text
import visidata.graph
import visidata.motd
import visidata.transpose
import visidata.shell
import visidata.layout
from .main import *
import visidata.help
import visidata.modify
import visidata.sort
import visidata.unfurl
import visidata.fill
import visidata.incr
import visidata.customdate
import visidata.misc
import visidata.memory
import visidata.macros
import visidata.macos

import visidata.loaders.csv
import visidata.loaders.archive
import visidata.loaders.xlsx
import visidata.loaders.xlsb
import visidata.loaders.hdf5
import visidata.loaders.sqlite
import visidata.loaders.fixed_width
import visidata.loaders.postgres
import visidata.loaders.mysql
import visidata.loaders.shp
import visidata.loaders.geojson
import visidata.loaders.mbtiles
import visidata.loaders.http
import visidata.loaders.html
import visidata.loaders.markdown
import visidata.loaders.pcap
import visidata.loaders.png
import visidata.loaders.ttf
import visidata.loaders.sas
import visidata.loaders.spss
import visidata.loaders.xml
import visidata.loaders.yaml
import visidata.loaders._pandas
import visidata.loaders.graphviz
import visidata.loaders.npy
import visidata.loaders.usv
import visidata.loaders.frictionless
import visidata.loaders.imap

import visidata.loaders.pdf
import visidata.loaders.pandas_freqtbl
import visidata.loaders.xword
import visidata.loaders.vcf
import visidata.loaders.texttables
import visidata.loaders.rec
import visidata.loaders.eml
import visidata.loaders.vds

import visidata.ddwplay
import visidata.plugins

import visidata.colorsheet

from .deprecated import *

try:
    import vdplus
except ModuleNotFoundError as e:
    pass

import math
from math import *

vd.finalInit()

vd.addGlobals(globals())
