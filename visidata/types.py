'''VisiData uses Python native int, float, str, and adds a simple date and anytype.

A type T is used internally in these ways:
    o = T(str)   # for conversion from string
    o = T()      # for default value to be used when conversion fails

The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).
'''

import datetime


# minimalist 'any' type
anytype = lambda r=None: str(r)
anytype.__name__ = ''


class date:
    'simple wrapper around datetime so it can be created from dateutil str or numeric input as time_t'
    def __init__(self, s=None):
        if s is None:
            self.dt = datetime.datetime.now()
        elif isinstance(s, int) or isinstance(s, float):
            self.dt = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            import dateutil.parser
            self.dt = dateutil.parser.parse(s)
        else:
            assert isinstance(s, datetime.datetime)
            self.dt = s

    def __str__(self):
        'always use ISO8601'
        return self.dt.strftime('%Y-%m-%d %H:%M:%S')

    def __lt__(self, a):
        return self.dt < a.dt


def detect_type(v):
    'auto-detect types in this order of preference: int float date str'
    def try_type(T, v):
        try:
            v = T(v)
            return T
        except:
            return None

    return try_type(int, v) or try_type(float, v) or try_type(date, v) or str
