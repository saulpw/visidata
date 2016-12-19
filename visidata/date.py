import datetime

class date:
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
        return self.dt.strftime('%Y-%m-%d %H:%M:%S')

    def __lt__(self, a):
        return self.dt < a.dt



