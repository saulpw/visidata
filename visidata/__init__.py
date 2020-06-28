'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '2.-4dev'
__version_info__ = 'VisiData v' + __version__
__author__ = 'Saul Pwanson <vd@saul.pw>'
__status__ = 'Production/Stable'
__copyright__ = 'Copyright (c) 2016-2019 ' + __author__


class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass


def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)


def getGlobals():
    return globals()

from builtins import *
from copy import copy, deepcopy

from .utils import *

from .extensible import *
from .vdobj import *

vd = VisiData()

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
from .movement import *
from .path import *
from .urlcache import *
from .selection import *
from .loaders.tsv import *
from .pyobj import *
from .loaders.json import *
from .data import *
from .save import *
from .clipboard import *
from .slide import *
from .search import *
from .expr import *

from .choose import *
from .metasheets import *
from .join import *
from .aggregators import *
from .describe import *
from .pivot import *
from .freqtbl import *
from .melt import *
from .cmdlog import *
from .freeze import *
from .regex import *
from .canvas import *
from .graph import *
from .motd import *
from .transpose import *
from .shell import *
from .layout import *
from .main import *
from .help import *
from .defermods import *
import visidata.sort

from .loaders.csv import *
from .loaders.archive import *
from .loaders.xlsx import *
from .loaders.xlsb import *
from .loaders.hdf5 import *
from .loaders.sqlite import *
from .loaders.fixed_width import *
from .loaders.postgres import *
from .loaders.mysql import *
from .loaders.shp import *
from .loaders.mbtiles import *
from .loaders.http import *
from .loaders.html import *
from .loaders.markdown import *
from .loaders.pcap import *
from .loaders.png import *
from .loaders.ttf import *
from .loaders.sas import *
from .loaders.spss import *
from .loaders.xml import *
from .loaders.yaml import *
from .loaders._pandas import *
from .loaders.graphviz import *
from .loaders.npy import *
from .loaders.usv import *
from .loaders.frictionless import *
from .loaders.imap import *

from .loaders.pandas_freqtbl import *
from .loaders.xword import *

from .plugins import *

from .colorsheet import *

from .deprecated import *

from math import *

vd.finalInit()

addGlobals(globals())
