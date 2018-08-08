import os
import os.path
import time
import urllib.request
import urllib.parse

from visidata import __version_info__, Path, options


def urlcache(url, cachesecs=24*60*60):
    'Returns Path object to local cache of url contents.'
    p = Path(os.path.join(options.visidata_dir, 'cache', urllib.parse.quote(url, safe='')))
    if p.exists():
        secs = time.time() - p.stat().st_mtime
        if secs < cachesecs:
            return p

    if not p.parent.exists():
        os.makedirs(p.parent.resolve(), exist_ok=True)

    assert p.parent.is_dir(), p.parent

    req = urllib.request.Request(url, headers={'User-Agent': __version_info__})
    with urllib.request.urlopen(req) as fp:
        ret = fp.read().decode('utf-8').strip()
        with p.open_text(mode='w') as fpout:
            fpout.write(ret)

    return p
