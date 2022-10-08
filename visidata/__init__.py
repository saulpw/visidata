'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '2.10.2'
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
import visidata.settings
from .errors import *
from .editor import *
from .cliptext import *
from .color import *
from .mainloop import *
from .wrappers import *
from .undo import *

from ._types import *
from .column import *

from .sheets import *

import visidata.statusbar

import visidata.textsheet
import visidata.threads
from .path import *
import visidata._input
import visidata.movement

import visidata._urlcache
import visidata.selection
import visidata.loaders.tsv
import visidata.pyobj
import visidata.loaders.json
import visidata._open
import visidata.metasheets
import visidata.cmdlog
import visidata.save
import visidata.clipboard
import visidata.slide
import visidata.search
import visidata.expr

import visidata.menu
import visidata.choose
import visidata.join
import visidata.aggregators
import visidata.describe
import visidata.pivot
import visidata.freqtbl
import visidata.melt
import visidata.freeze
import visidata.regex
import visidata.canvas
import visidata.canvas_text
import visidata.graph
import visidata.motd
import visidata.transpose
import visidata.shell
import visidata.layout
import visidata.main
import visidata.help
import visidata.modify
import visidata.sort
import visidata.unfurl
import visidata.fill
import visidata.incr
import visidata.window
import visidata.customdate
import visidata.misc
import visidata.memory
import visidata.macros
import visidata.macos
import visidata.repeat

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
import visidata.loaders.odf
import visidata.loaders.lsv
import visidata.loaders.arrow
import visidata.loaders.parquet

import visidata.loaders.vdx

import visidata.form

import visidata.ddwplay
import visidata.plugins

import visidata.colorsheet

from .deprecated import *

import math
import random
from math import *

vd.finalInit()

vd.addGlobals(globals())
