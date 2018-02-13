from visidata import *


@async
def domotd():
    try:
        domotd_sync()
    except Exception as e:
        pass


def domotd_sync():
    motd = None
    p = Path('~/.visidata.motd')
    if p.exists():
        import time
        secs = time.time() - p.stat().st_mtime
        if secs < 3600*24:
            motd = p.read_text().strip()

    if motd is None:
        import urllib.request
        with urllib.request.urlopen('http://visidata.org/motd') as fp:
            motd = fp.read().decode('utf-8').strip()
            with p.open_text(mode='w') as fpout:
                fpout.write(motd)

    vd().motd = motd
    status(*motd.splitlines())


domotd()
