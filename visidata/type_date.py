import datetime

from visidata import vd, Sheet

try:
    from dateutil.parser import parse as date_parse
except ImportError:
    def date_parse(r=''):
        vd.warning('install python-dateutil for date type')
        return r


vd.option('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values', replay=True)


@vd.numericType('@', '', formatter=lambda fmtstr,val: val.strftime(fmtstr or vd.options.disp_date_fmt))
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
        if isinstance(b, datetime.datetime): return datetime.datetime.__ge__(self, b)
        elif isinstance(b, datetime.date):   return self.date().__ge__(b)
        return NotImplemented

    def __eq__(self, b):
        if isinstance(b, datetime.datetime): return datetime.datetime.__eq__(self, b)
        elif isinstance(b, datetime.date): return self.date().__eq__(b)
        return NotImplemented

    def __str__(self):
        return self.strftime(vd.options.disp_date_fmt)

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


# simple constants, for expressions like 'timestamp+15*minutes'
vd.addGlobals(
    years=365.25,
    months=30.0,
    weeks=7.0,
    days=1.0,
    hours=1.0/24,
    minutes=1.0/(24*60),
    seconds=1.0/(24*60*60),
    datedelta=datedelta)


Sheet.addCommand('@', 'type-date', 'cursorCol.type = date', 'set type of current column to date')
