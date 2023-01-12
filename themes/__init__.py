'Auto-import all modules in themes directory.'

import pkgutil
import os.path

__all__ = list(module for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]))

from . import *

