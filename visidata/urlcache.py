from visidata import *

import urllib.request
import urllib.parse
import os.path


@functools.lru_cache()
def urlcache(url, cachesecs=24*60*60):
    p = Path(os.path.join(options.visidata_dir, 'cache', urllib.parse.quote(url, safe='')))
    if p.exists():
        secs = time.time() - p.stat().st_mtime
        if secs < cachesecs:
            return p.read_text()

    if not p.parent.exists():
        os.mkdir(p.parent.resolve())

    assert p.parent.is_dir(), p.parent

    with urllib.request.urlopen(url) as fp:
        ret = fp.read().decode('utf-8').strip()
        with p.open_text(mode='w') as fpout:
            fpout.write(ret)

    return ret
