# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.

import functools
import datetime
from visidata import options, theme

from .vdtui import vdtype

try:
    import dateutil.parser
except ImportError:
    pass


theme('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values')


floatchars='+-0123456789.'
def currency(s=''):
    'dirty float (strip non-numeric characters)'
    if isinstance(s, str):
        s = ''.join(ch for ch in s if ch in floatchars)
    return float(s) if s else float()

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
        elif isinstance(s, datetime.datetime):
            r = s
        else:
            raise Exception('invalid type for date')

        t = r.timetuple()
        return super().__new__(cls, *t[:6], tzinfo=r.tzinfo)

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
        return super().__add__(n)

    def __sub__(self, n):
        'subtract n days (int or float) from the date'
        if isinstance(n, (int, float)):
            n = datetime.timedelta(days=n)
        return super().__sub__(n)

vdtype(date, '@', '', formatter=lambda fmtstr,val: val.strftime(fmtstr or options.disp_date_fmt))
vdtype(currency, '$', '{:,.02f}')

# simple constants, for expressions like 'timestamp+15*minutes'
years=365.25
months=30.0
weeks=7.0
days=1.0
hours=days/24
minutes=days/(24*60)
seconds=days/(24*60*60)
