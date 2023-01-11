from visidata import *

from .git import *
from .status import *
from .merge import *
from .blame import *
from .diff import *
from .repo import *
from .amend import *
from .grep import *
from .overview import *

vd.addGlobals(globals())
