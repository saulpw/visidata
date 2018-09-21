from visidata import *
from visidata import __version__

option('motd_url', 'https://visidata.org/motd-'+__version__, 'source of randomized startup messages')


earthdays = lambda n: n*24*60*60


@asyncthread
def domotd():
    try:
        if options.motd_url:
            p = urlcache(options.motd_url, earthdays(1))
            line = random.choice(list(p))
            status(line.split('\t')[0], priority=-1)
    except Exception:
        pass
