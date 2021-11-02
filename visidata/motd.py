'''motd: display a low-priority random Message Of The Day on startup.

Call `domotd()` to spawn an asyncthread to read and/or fetch
a motd file from a url.  The file may be text or unheaded TSV, with one message per row in the first column.

Any Exception ends the thread silently.

options.motd_url may be set to another URL, or empty to disable entirely.
'''

import random

from visidata import options, asyncsingle, vd, VisiData

vd.option('motd_url', 'https://visidata.org/motd-'+vd.version, 'source of randomized startup messages', sheettype=None)


vd.motd = ''

@VisiData.api
@asyncsingle
def domotd(vd):
    try:
        if options.motd_url:
            p = vd.urlcache(options.motd_url, days=1)
            line = random.choice(list(p))
            vd.motd = line.split('\t')[0]
            vd.status(vd.motd, priority=-1)
    except Exception:
        pass
