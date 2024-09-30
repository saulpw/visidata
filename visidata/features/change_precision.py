__author__ = 'Andy Craig, andycraig (https://github.com/andycraig)'


import re

from visidata import vd, Sheet, Column, floatsi, currency, date

date_fmtstrs = [
    '%Y',
    '%Y-%m',
#    '%Y-W%U',
    '%Y-%m-%d',
    '%Y-%m-%d %H',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%f',
]

@Column.api
def setcol_precision(col, amount:int):
    if col.type is date:
        try:
            i = date_fmtstrs.index(col.fmtstr)
        except ValueError:
            i = 2
        col.fmtstr = date_fmtstrs[(i+amount)%len(date_fmtstrs)]
    elif col.type in (float, floatsi, currency):
        if col.fmtstr == '':
            col.fmtstr = f'%.{2 + amount}f'
        else:
            precision_str = re.match(r'%.([0-9]+)f', col.fmtstr)
            if not precision_str is None:
                col.fmtstr = f'%.{max(0, int(precision_str[1]) + amount)}f'
    else:
        vd.fail('column type must be numeric or date')


vd.addMenuItems('''
    Column > Set precision > more > setcol-precision-more
    Column > Set precision > less > setcol-precision-less
''')

Sheet.addCommand('Alt+-', 'setcol-precision-less', 'cursorCol.setcol_precision(-1)', 'show less precision in current column')
Sheet.addCommand('Alt++', 'setcol-precision-more', 'cursorCol.setcol_precision(1)', 'show more precision in current column')
