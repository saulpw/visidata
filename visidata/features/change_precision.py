__author__ = 'Andy Craig, andycraig (https://github.com/andycraig)'


import re

from visidata import VisiData, vd, Sheet, Column, floatsi, currency, date

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
            m = re.fullmatch(r'\{:\.([0-9]+)f\}|%\.([0-9]+)f', col.fmtstr)
            if not m:
                vd.fail(f'could not parse column fmtstr')
            if m[1]:
                col.fmtstr = '{:.' + f'{max(0, int(m[1]) + amount)}f' + '}'
            elif m[2]:
                col.fmtstr =       f'%.{max(0, int(m[2]) + amount)}f'
    else:
        vd.fail('column type must be numeric or date')

@VisiData.api
def setcol_precision_input(vd):
     m = re.fullmatch(r'\{:\.([0-9]+)f\}|%\.([0-9]+)f', vd.options.disp_float_fmt)
     if not m:
         vd.fail('could not parse disp_float_fmt')
     precision = max(0, int(vd.input("float precision=", value="2")))
     if m[1]:
         vd.options.disp_float_fmt = '{:.' + str(precision) + 'f}'
     elif m[2]:
         vd.options.disp_float_fmt = '%.0' + str(precision) + 'f'

vd.addMenuItems('''
    Column > Set precision > more > setcol-precision-more
    Column > Set precision > less > setcol-precision-less
''')

Sheet.addCommand('Alt+-', 'setcol-precision-less', 'cursorCol.setcol_precision(-1)', 'show less precision in current column')
Sheet.addCommand('Alt++', 'setcol-precision-more', 'cursorCol.setcol_precision(1)', 'show more precision in current column')
Sheet.addCommand('g%', 'setcol-precision-input', 'vd.setcol_precision_input()', 'change the number of decimal places shown for floats')
