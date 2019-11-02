# uses API from nettoolkit.com

'''Set options.ntk_key='<api-key>', then use command "geocode-col" on a column
with placename, to add a "geocodes" column with a list of potential geocoded
places, and lat/long columns with the actual coords of the first of those.'''

__author__='Saul Pwanson <vd+geocode@saul.pw>'
__version__='0.1'

import urllib.parse
import json

from visidata import vd, urlcache, AttrDict, Sheet, option, options, Column, ColumnExpr

option('ntk_key', '', 'API Key for nettoolkit.com')


def geocode(addr):
    'Return (Lat, Long) as namedlist of floats.'
    url = 'https://api.nettoolkit.com/v1/geo/geocodes?address='+urllib.parse.quote(addr, safe='')
    resp = urlcache(url, headers={'X-NTK-KEY': options.ntk_key})
    return json.loads(resp.read_text())['results']


@Sheet.api
def geocode_col(sheet, vcolidx):
    col = sheet.visibleCols[vcolidx]

    for c in [
        Column('geocodes', origCol=col, cache='async',
               getter=lambda c,r: geocode(c.origCol.getDisplayValue(r))),
        ColumnExpr('lat', cache=False, expr='geocodes[0]["latitude"]'),
        ColumnExpr('long', cache=False, expr='geocodes[0]["longitude"]'),
            ]:
        sheet.addColumn(c, index=vcolidx+1)


Sheet.addCommand('', 'geocode-col', 'sheet.geocode_col(cursorVisibleColIndex)')
