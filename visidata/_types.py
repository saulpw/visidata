# VisiData uses Python native int, float, str, and adds simple anytype.

import locale
from visidata import options, TypedWrapper, vd, VisiData

#__all__ = ['anytype', 'vdtype', ]

vd.option('disp_float_fmt', '{:.02f}', 'default fmtstr to format for float values', replay=True)
vd.option('disp_int_fmt', '{:.0f}', 'default fmtstr to format for int values', replay=True)

vd.numericTypes = [int,float]

# VisiDataType .typetype are e.g. int, float, str, and used internally in these ways:
#
#    o = typetype(val)   # for interpreting raw value
#    o = typetype(str)   # for conversion from string (when setting)
#    o = typetype()      # for default value to be used when conversion fails
#
# The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).
#
# .icon is a single character that appears in the notes field of cells and column headers.
# .formatter(fmtstr, typedvalue) returns a string of the formatted typedvalue according to fmtstr.
# .fmtstr is the default fmtstr passed to .formatter.

def anytype(r=None):
    'minimalist "any" passthrough type'
    return r
anytype.__name__ = ''


@VisiData.global_api
def numericFormatter(vd, fmtstr, typedval):
    try:
        fmtstr = fmtstr or options['disp_'+type(typedval).__name__+'_fmt']
        if fmtstr[0] == '%':
            return locale.format_string(fmtstr, typedval, grouping=False)
        else:
            return fmtstr.format(typedval)
    except ValueError:
        return str(typedval)


@VisiData.api
def numericType(vd, icon='', fmtstr='', formatter=vd.numericFormatter):
    '''Decorator for numeric types.'''
    def _decorator(f):
        vd.addType(f, icon=icon, fmtstr=fmtstr, formatter=formatter)
        vd.numericTypes.append(f)
        vd.addGlobals({f.__name__: f})
        return f
    return _decorator


class VisiDataType:
    'Register *typetype* in the typemap.'
    def __init__(self, typetype=None, icon=None, fmtstr='', formatter=vd.numericFormatter, key='', name=None):
        self.typetype = typetype or anytype # int or float or other constructor
        self.name = name or getattr(typetype, '__name__', str(typetype))
        self.icon = icon      # show in rightmost char of column
        self.fmtstr = fmtstr
        self.formatter = formatter
        self.key = key

@VisiData.api
def addType(vd, typetype=None, icon=None, fmtstr='', formatter=vd.numericFormatter, key='', name=None):
    '''Add type to type map.

    - *typetype*: actual type class *TYPE* above
    - *icon*: unicode character in column header
    - *fmtstr*: format string to use if fmtstr not given
    - *formatter*: formatting function to call as ``formatter(fmtstr, typedvalue)``
    '''
    t = VisiDataType(typetype=typetype, icon=icon, fmtstr=fmtstr, formatter=formatter, key=key, name=name)
    if typetype:
        vd.typemap[typetype] = t
    return t

vdtype = vd.addType


# typemap [vtype] -> VisiDataType
vd.typemap = {}

@VisiData.api
def getType(vd, typetype):
    return vd.typemap.get(typetype) or VisiDataType()

vdtype(None, '∅')
vdtype(anytype, '', formatter=lambda _,v: str(v))
vdtype(str, '~', formatter=lambda _,v: v)
vdtype(int, '#')
vdtype(float, '%')
vdtype(dict, '')
vdtype(list, '')

@VisiData.api
def isNumeric(vd, col):
    return col.type in vd.numericTypes

##

@vd.numericType('%')
def floatlocale(*args):
    'Calculate float() using system locale set in LC_NUMERIC.'
    if not args:
        return 0.0

    return locale.atof(*args)


@vd.numericType('♯', fmtstr='%.0f')
class vlen(int):
    def __new__(cls, v=0):
        if isinstance(v, (vlen, int, float)):
            return super(vlen, cls).__new__(cls, v)
        else:
            return super(vlen, cls).__new__(cls, len(v))

    def __len__(self):
        return self
