'Auto-import all modules in features directory.'

import pkgutil
import os.path

from visidata import vd


for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    vd.importModule(__package__, module)
