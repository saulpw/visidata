import os
import os.path
import time

from visidata import vd, VisiData, Path, modtime
from visidata.settings import _get_cache_dir


@VisiData.global_api
def urlcache(vd, url, days=1, text=True, headers={}):
    'Return Path object to local cache of url contents.'
    from urllib.request import Request, urlopen
    import urllib.parse

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
            with p.open(mode='w', encoding='utf-8') as fpout:
                fpout.write(ret)
        else:
            with p.open_bytes(mode='w') as fpout:
                fpout.write(ret)

    return p


@VisiData.api
def enable_requests_cache(vd):
    try:
        import requests
        import requests_cache

        requests_cache.install_cache(str(Path(os.path.join(vd.options.visidata_dir, 'httpcache'))), backend='sqlite', expire_after=24*60*60)
    except ModuleNotFoundError:
        vd.warning('install requests_cache for less intrusive scraping')


vd.addGlobals({'urlcache': urlcache})
