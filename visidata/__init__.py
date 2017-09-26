
'VisiData: a curses interface for exploring and arranging tabular data'

from .vdtui import __version__
from .vdtui import *
from .async import *
from .zscroll import *
from .aggregators import *
from .data import *
from .clipboard import *

from .freqtbl import *
from .describe import *
from .pyobj import *
from .metasheets import *
from .pivot import *
from .tidydata import *
from .cmdlog import *
from .freeze import *
from .regex import *

from .loaders.csv import *
from .loaders.zip import *
from .loaders.xlsx import *
from .loaders.hdf5 import *
from .loaders.sqlite import *
from .loaders.fixed_width import *
from .loaders.postgres import *

addGlobals(globals())
