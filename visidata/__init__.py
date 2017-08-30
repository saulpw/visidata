
'VisiData: a curses interface for exploring and arranging tabular data'

from .vdtui import __version__
from .vdtui import *
from .async import *
from .zscroll import *
from .data import *
from .clipboard import *

from .addons.freqtbl import *
from .addons.describe import *
from .addons.pyobj import *
from .addons.metasheets import *
from .addons.pivot import *
from .addons.tidydata import *
from .addons.editlog import *
from .addons.freeze import *
from .addons.regex import *

from .loaders.csv import *
from .loaders.zip import *
from .loaders.xlsx import *
from .loaders.hdf5 import *
from .loaders.sqlite import *
from .loaders.fixed_width import *

addGlobals(globals())
