# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.

import functools
import datetime
import locale
from visidata import options, theme, Sheet, TypedWrapper, undoAttr
from visidata import vdtype

try:
    import dateutil.parser
except ImportError:
    pass


theme('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values')

undoColType = undoAttr('[cursorCol]', 'type')

Sheet.addCommand('z~', 'type-any', 'cursorCol.type = anytype', undo=undoColType),
Sheet.addCommand('~', 'type-string', 'cursorCol.type = str', undo=undoColType),
Sheet.addCommand('@', 'type-date', 'cursorCol.type = date', undo=undoColType),
Sheet.addCommand('#', 'type-int', 'cursorCol.type = int', undo=undoColType),
Sheet.addCommand('z#', 'type-len', 'cursorCol.type = vlen', undo=undoColType),
Sheet.addCommand('$', 'type-currency', 'cursorCol.type = currency', undo=undoColType),
Sheet.addCommand('%', 'type-float', 'cursorCol.type = float', undo=undoColType),

floatchars='+-0123456789.'
def currency(s=''):
    'dirty float (strip non-numeric characters)'
    if isinstance(s, str):
        s = ''.join(ch for ch in s if ch in floatchars)
    return float(s) if s else TypedWrapper(float, None)


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
vdtype(currency, '$', formatter=lambda fmtstr,val: locale.currency(val, symbol=False))

# simple constants, for expressions like 'timestamp+15*minutes'
years=365.25
months=30.0
weeks=7.0
days=1.0
hours=days/24
minutes=days/(24*60)
seconds=days/(24*60*60)
