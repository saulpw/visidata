import os
import os.path
import time
from urllib.request import Request, urlopen
import urllib.parse

from visidata import vd, VisiData, Path, options, modtime
from visidata.settings import _get_cache_dir

@VisiData.global_api
def urlcache(vd, url, days=1, text=True, headers={}):
    'Return Path object to local cache of url contents.'
    cache_dir = _get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)

    p = Path(cache_dir / urllib.parse.quote(url, safe=''))
    if p.exists():
        secs = time.time() - modtime(p)
        if secs < days*24*60*60:
            return p

    req = Request(url)
    for k, v in headers.items():
        req.add_header(k, v)

    with urlopen(req) as fp:
        ret = fp.read()
        if text:
            ret = ret.decode('utf-8').strip()
            with p.open_text(mode='w', encoding='utf-8') as fpout:
                fpout.write(ret)
        else:
            with p.open_bytes(mode='w') as fpout:
                fpout.write(ret)

    return p


vd.addGlobals({'urlcache': urlcache})
