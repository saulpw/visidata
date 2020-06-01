# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.

import collections
import functools
import datetime
import locale
from visidata import option, options, TypedWrapper, vd

#__all__ = ['anytype', 'vdtype', 'typemap', 'getType', 'typemap']

option('disp_currency_fmt', '%.02f', 'default fmtstr to format for currency values', replay=True)
option('disp_float_fmt', '{:.02f}', 'default fmtstr to format for float values', replay=True)
option('disp_int_fmt', '{:.0f}', 'default fmtstr to format for int values', replay=True)
option('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values', replay=True)

try:
    import dateutil.parser
except ImportError:
    pass

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
    fmtstr = fmtstr or options['disp_'+type(typedval).__name__+'_fmt']
    if fmtstr:
        if fmtstr[0] == '%':
            return locale.format_string(fmtstr, typedval, grouping=True)
        else:
            return fmtstr.format(typedval)
    return str(typedval)


class VisiDataType:
    def __init__(self, typetype=None, icon=None, fmtstr='', formatter=numericFormatter, key='', name=None):
        self.typetype = typetype or anytype # int or float or other constructor
        self.name = name or getattr(typetype, '__name__', str(typetype))
        self.icon = icon      # show in rightmost char of column
        self.fmtstr = fmtstr
        self.formatter = formatter
        self.key = key

        if typetype:
            typemap[typetype] = self

vdtype = VisiDataType

# typemap [vtype] -> VisiDataType
typemap = {}

def getType(typetype):
    return typemap.get(typetype) or VisiDataType()

vdtype(None, '∅')
vdtype(anytype, '', formatter=lambda _,v: str(v))
vdtype(str, '~', formatter=lambda _,v: v)
vdtype(int, '#')
vdtype(float, '%')
vdtype(dict, '')
vdtype(list, '')

def isNumeric(col):
    return col.type in (int,vlen,float,currency,date)

##

floatchars='+-0123456789.'
class currency(float):
    def __new__(self, s=''):
        'dirty float (strip non-numeric characters)'
        if isinstance(s, str):
            s = ''.join(ch for ch in s if ch in floatchars)
        return float.__new__(self, s)


class vlen(int):
    def __new__(cls, v):
        if isinstance(v, (vlen, int, float)):
            return super(vlen, cls).__new__(cls, v)
        else:
            return super(vlen, cls).__new__(cls, len(v))

    def __len__(self):
        return self


class date(datetime.datetime):
    'datetime wrapper, constructed from time_t or from str with dateutil.parse'

    def __new__(cls, s=None):
        'datetime is immutable so needs __new__ instead of __init__'
        if s is None:
            r = datetime.datetime.now()
        elif isinstance(s, int) or isinstance(s, float):
            r = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            r = dateutil.parser.parse(s)
        elif isinstance(s, (datetime.datetime, datetime.date)):
            r = s
        else:
            raise Exception('invalid type for date %s' % type(s).__name__)

        t = r.timetuple()
        ms = getattr(r, 'microsecond', 0)
        tzinfo = getattr(r, 'tzinfo', None)
        return super().__new__(cls, *t[:6], microsecond=ms, tzinfo=tzinfo)

    def __str__(self):
        return self.strftime(options.disp_date_fmt)

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
vdtype(date, '@', '', formatter=lambda fmtstr,val: val.strftime(fmtstr or options.disp_date_fmt))
vdtype(currency, '$')

# simple constants, for expressions like 'timestamp+15*minutes'
years=365.25
months=30.0
weeks=7.0
days=1.0
hours=days/24
minutes=days/(24*60)
seconds=days/(24*60*60)
