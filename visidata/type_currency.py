from visidata import vd, Sheet

vd.option('disp_currency_fmt', '%.02f', 'default fmtstr to format for currency values', replay=True)


floatchars='+-0123456789.'

@vd.numericType('$')
def currency(*args):
    'dirty float (strip non-numeric characters)'
    if args and isinstance(args[0], str):
        args = [''.join(ch for ch in args[0] if ch in floatchars)]
    return float(*args)


Sheet.addCommand('$', 'type-currency', 'cursorCol.type = currency', 'set type of current column to currency')
