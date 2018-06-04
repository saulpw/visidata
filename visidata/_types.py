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
        else:
            assert isinstance(s, datetime.datetime), type(s)
            r = s

        t = r.timetuple()
        return super().__new__(cls, *t[:6], tzinfo=r.tzinfo)

    def __str__(self):
        return self.strftime(options.disp_date_fmt)

    def __float__(self):
        return self.timestamp()


vdtype(date, '@', '', formatter=lambda fmtstr,val: val.strftime(fmtstr or options.disp_date_fmt))
vdtype(currency, '$', '{:,.02f}')
