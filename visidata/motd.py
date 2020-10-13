'''motd: display a low-priority random Message Of The Day on startup.

Call `domotd()` to spawn an asyncthread to read and/or fetch
a motd file from a url.  The file may be text or unheaded TSV, with one message per row in the first column.

Any Exception ends the thread silently.

options.motd_url may be set to another URL, or empty to disable entirely.
'''

import random

from visidata import option, options, asyncsingle, urlcache, vd
from visidata import __version__

option('motd_url', 'https://visidata.org/motd-'+__version__, 'source of randomized startup messages', sheettype=None)


@asyncsingle
def domotd():
    try:
        if options.motd_url:
            p = urlcache(options.motd_url, days=1)
            line = random.choice(list(p))
            vd.status(line.split('\t')[0], priority=-1)
    except Exception:
        pass
