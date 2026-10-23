'''Exact decimal arithmetic for money and other fixed-point numbers.  #2396

No keys are bound; bind one in .visidatarc, for example:

    Sheet.bindkey('z$', 'type-decimal')
'''

from decimal import Decimal

from visidata import vd, Sheet, ColumnsSheet

vd.option('disp_decimal_fmt', '{}', 'default fmtstr to format decimal values', replay=True, help=vd.help_float_fmt)

decimalchars = '+-0123456789.'


def formatDecimal(fmtstr, val):
    return vd.numericFormatter(fmtstr or vd.options.disp_decimal_fmt, val)


@vd.numericType('$', formatter=formatDecimal)
def decimal(*args):
    'dirty decimal (strip non-numeric characters)'
    if not args:
        return Decimal()
    v = args[0]
    if isinstance(v, str):
        v = ''.join(ch for ch in v if ch in decimalchars)
    elif isinstance(v, float):
        v = repr(v)
    return Decimal(v)


vd.addType(Decimal, icon='$', formatter=formatDecimal, name='Decimal')

Sheet.addCommand('', 'type-decimal', 'cursorCol.type=decimal', 'set type of current column to decimal')
ColumnsSheet.addCommand('', 'type-decimal-selected', 'onlySelectedRows.type=decimal', 'set type of selected source columns to decimal')

vd.addMenuItems('''
    Column > Type as > decimal > type-decimal
''')
