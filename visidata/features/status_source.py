import inspect

import visidata
from visidata import VisiData

@VisiData.api
def getStatusSource(vd):
    if not vd.options.debug:
        return ''
    stack = inspect.stack(context=0)  #2370
    for i, sf in enumerate(stack):
        if sf.function in 'status aside'.split():
            if stack[i+1].function in 'error fail warning debug'.split():
                sf = stack[i+2]
            else:
                sf = stack[i+1]
            break

    fn = sf.filename
    if fn.startswith(visidata.__path__[0]):
        fn = visidata.__package__ + fn[len(visidata.__path__[0]):]
    return f'{fn}:{sf.lineno}:{sf.function}'
