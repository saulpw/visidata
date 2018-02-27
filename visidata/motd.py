from visidata import *

option('motd_url', 'http://visidata.org/motd', 'source of randomized startup messages')


@diskcache('motd', 24*3600)
def motd(url):
    import urllib.request
    with urllib.request.urlopen(url) as fp:
        return fp.read().decode('utf-8').strip()


@async
def domotd():
    try:
        if options.motd_url:
            line = random.choice(motd(options.motd_url).splitlines())
            status(line.split('\t')[0])
    except Exception:
        pass


domotd()
