
'VisiData: a curses interface for exploring and arranging tabular data'

from .vd import __version__
from .vd import *
from .addons.freqtbl import *
from .addons.pyobj import *
from .addons.metasheets import *
from .addons.pivot import *
from .addons.tidydata import *
from .addons.editlog import *
from .addons.freeze import *
from .addons.regex import *

from .addons.csv import *
from .addons.zip import *
from .addons.xlsx import *
from .addons.hdf5 import *
from .addons.sqlite import *
#from .addons.gsheets import *
#from .addons.blaze import *


set_globals(globals())
