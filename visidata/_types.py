# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.

import collections
import functools
import datetime
import locale
from visidata import options, TypedWrapper, vd, VisiData

#__all__ = ['anytype', 'vdtype', ]

vd.option('disp_currency_fmt', '%.02f', 'default fmtstr to format for currency values', replay=True)
vd.option('disp_float_fmt', '{:.02f}', 'default fmtstr to format for float values', replay=True)
vd.option('disp_int_fmt', '{:.0f}', 'default fmtstr to format for int values', replay=True)
vd.option('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values', replay=True)

try:
    from dateutil.parser import parse as date_parse
except ImportError:
    def date_parse(r=''):
        vd.warning('install python-dateutil for date type')
        return r

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


def numericFormatter(fmtstr, typedval):
    try:
        fmtstr = fmtstr or options['disp_'+type(typedval).__name__+'_fmt']
        if fmtstr[0] == '%':
            return locale.format_string(fmtstr, typedval, grouping=False)
        else:
            return fmtstr.format(typedval)
    except ValueError:
        return str(typedval)


vd.si_prefixes='p n u m . kK M G T P Q'.split()

def floatsi(*args):
    if not args:
        return 0.0
    if not isinstance(args[0], str):
        return args[0]

    s=args[0].strip()
    for i, p in enumerate(vd.si_prefixes):
        if s[-1] in p:
            return float(s[:-1]) * (1000 ** (i-4))

    return float(s)


def SIFormatter(fmtstr, val):
    level = 4
    if val != 0:
        while abs(val) > 1000:
            val /= 1000
            level += 1
        while abs(val) < 0.001:
            val *= 1000
            level -= 1

    return numericFormatter(fmtstr, val) + (vd.si_prefixes[level][0] if level != 4 else '')


class VisiDataType:
    'Register *typetype* in the typemap.'
    def __init__(self, typetype=None, icon=None, fmtstr='', formatter=numericFormatter, key='', name=None):
        self.typetype = typetype or anytype # int or float or other constructor
        self.name = name or getattr(typetype, '__name__', str(typetype))
        self.icon = icon      # show in rightmost char of column
        self.fmtstr = fmtstr
        self.formatter = formatter
        self.key = key

@VisiData.api
def addType(vd, typetype=None, icon=None, fmtstr='', formatter=numericFormatter, key='', name=None):
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
    return col.type in (int,vlen,float,currency,date,floatsi,floatlocale)

##

floatchars='+-0123456789.'
def currency(*args):
    'dirty float (strip non-numeric characters)'
    if args and isinstance(args[0], str):
        args = [''.join(ch for ch in args[0] if ch in floatchars)]
    return float(*args)

def floatlocale(*args):
    'Calculate float() using system locale set in LC_NUMERIC.'
    if not args:
        return 0.0

    return locale.atof(*args)


class vlen(int):
    def __new__(cls, v=0):
        if isinstance(v, (vlen, int, float)):
            return super(vlen, cls).__new__(cls, v)
        else:
            return super(vlen, cls).__new__(cls, len(v))

    def __len__(self):
        return self


class date(datetime.datetime):
    'datetime wrapper, constructed from time_t or from str with dateutil.parse'

    def __new__(cls, *args, **kwargs):
        'datetime is immutable so needs __new__ instead of __init__'
        if not args:
            return datetime.datetime.now()
        elif len(args) > 1:
            return super().__new__(cls, *args, **kwargs)

        s = args[0]
        if isinstance(s, int) or isinstance(s, float):
            r = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            r = date_parse(s)
        elif isinstance(s, (datetime.datetime, datetime.date)):
            r = s
        else:
            raise Exception('invalid type for date %s' % type(s).__name__)

        t = r.timetuple()
        ms = getattr(r, 'microsecond', 0)
        tzinfo = getattr(r, 'tzinfo', None)
        return super().__new__(cls, *t[:6], microsecond=ms, tzinfo=tzinfo, **kwargs)

    def __lt__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__lt__(self, b)
        elif isinstance(b, datetime.date):   return not self.date().__eq__(b) and self.date().__lt__(b)
        return NotImplemented

    def __gt__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__gt__(self, b)
        elif isinstance(b, datetime.date):   return not self.date().__eq__(b) and self.date().__gt__(b)
        return NotImplemented

    def __le__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__le__(self, b)
        elif isinstance(b, datetime.date):   return self.date().__le__(b)
        return NotImplemented

    def __ge__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__le__(self, b)
        elif isinstance(b, datetime.date):   return self.date().__ge__(b)
        return NotImplemented

    def __eq__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__eq__(self, b)
        elif isinstance(b, datetime.date): return self.date().__eq__(b)
        return NotImplemented

    def __str__(self):
        return self.strftime(options.disp_date_fmt)

    def __hash__(self):
        return super().__hash__()

    def __float__(self):
        return self.timestamp()

    def __radd__(self, n):
        return self.__add__(n)

    def __add__(self, n):
        'add n days (int or float) to the date'
        if isinstance(n, (int, float)):
            n = datetime.timedelta(days=n)
        return date(super().__add__(n))

    def __sub__(self, n):
        'subtract n days (int or float) from the date.  or subtract another date for a timedelta'
        if isinstance(n, (int, float)):
            n = datetime.timedelta(days=n)
        elif isinstance(n, (date, datetime.datetime)):
            return datedelta(super().__sub__(n).total_seconds()/(24*60*60))
        return super().__sub__(n)

class datedelta(datetime.timedelta):
    def __float__(self):
        return self.total_seconds()

vdtype(vlen, '♯', '%.0f')
vdtype(floatlocale, '%')
vdtype(date, '@', '', formatter=lambda fmtstr,val: val.strftime(fmtstr or options.disp_date_fmt))
vdtype(currency, '$')
vdtype(floatsi, '‱', formatter=SIFormatter)

# simple constants, for expressions like 'timestamp+15*minutes'
years=365.25
months=30.0
weeks=7.0
days=1.0
hours=days/24
minutes=days/(24*60)
seconds=days/(24*60*60)
