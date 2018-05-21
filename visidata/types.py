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

@functools.total_ordering
class date:
    'datetime wrapper, constructed from time_t or from str with dateutil.parse'

    def __init__(self, s=None):
        if s is None:
            self.dt = datetime.datetime.now()
        elif isinstance(s, int) or isinstance(s, float):
            self.dt = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            self.dt = dateutil.parser.parse(s)
        elif isinstance(s, date):
            self.dt = s.dt
        else:
            assert isinstance(s, datetime.datetime), (type(s), s)
            self.dt = s

    def to_string(self, fmtstr=None):
        'Convert datetime object to string, using options.disp_date_fmt.'
        if not fmtstr:
            fmtstr = options.disp_date_fmt
        return self.dt.strftime(fmtstr)

    def __getattr__(self, k):
        'Forward unknown attributes to inner datetime object'
        return getattr(self.dt, k)

    def __str__(self):
        return self.to_string()
    def __hash__(self):
        return hash(self.dt)
    def __float__(self):
        return self.dt.timestamp()
    def __lt__(self, a):
        return self.dt < a.dt
    def __eq__(self, a):
        return self.dt == a.dt
    def __sub__(self, a):
        return self.dt - a.dt
    def __add__(self, a):
        return date(self.dt + a)


vdtype(date, '@', '%Y-%m-%d', formatter=lambda fmtstr,val: val.to_string(fmtstr))
vdtype(currency, '$', '{:,.02f}')
