'''
Open .py files by importing them and pushing a pyobj sheet of the module object.
'''

import visidata

def open_py(p):
    import importlib
    return visidata.PyobjSheet(p.name, source=importlib.import_module('.'.join(list(p.parts[:-1]) + [p.name])))
