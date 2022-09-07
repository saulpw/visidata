import os
import os.path
import time
from urllib.request import Request, urlopen
import urllib.parse
import requests

from visidata import vd, VisiData, Path, options, modtime
from visidata.settings import _get_cache_dir

import logging
logging.basicConfig(filename='/tmp/urlcache.log', level=logging.DEBUG)

@VisiData.global_api
def urlcache(vd, url, days=1, text=True, headers={}, http_library='urllib'):
    'Return Path object to local cache of url contents.'
    assert http_library in ['urllib', 'requests'], "http_library %s should be one of 'urllib' or 'requests'"
    assert not (http_library == 'requests' and text == False), "requests library only implemented for textual requests"

    logging.info("urlcache url=%s days=%s text=%s headers=%s" % (url, days, text, headers))
    cache_dir = _get_cache_dir()
    logging.info("cache_dir %s" % (cache_dir,))
    os.makedirs(cache_dir, exist_ok=True)

    p = Path(cache_dir / urllib.parse.quote(url, safe=''))
    logging.info("Path %s" % (p, ))
    if p.exists():
        logging.info("exists, use cached version")
        secs = time.time() - modtime(p)
        if secs < days*24*60*60:
            return p

    if http_library == 'urllib':
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
    elif http_library == 'requests':
        response = requests.request("GET", url, headers=headers)
        with p.open_text(mode="w", encoding="utf-8") as fpout:
            fpout.write(response.text)

    return p


vd.addGlobals({'urlcache': urlcache})
