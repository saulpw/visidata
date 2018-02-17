from visidata import *


@diskcache('motd', 3600*24)
def motd():
    import urllib.request
    with urllib.request.urlopen('http://visidata.org/motd') as fp:
        return fp.read().decode('utf-8').strip()


@async
def domotd():
    try:
        status(*motd().splitlines())
    except Exception as e:
        pass


domotd()
