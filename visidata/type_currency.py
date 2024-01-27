from visidata import vd, Sheet, Column

vd.option('disp_currency_fmt', '%.02f', 'default fmtstr to format for currency values', replay=True, help=vd.help_float_fmt)
vd.theme_option('color_currency_neg', 'red', 'color for negative values in currency displayer', replay=True)


floatchars='+-0123456789.'

@vd.numericType('$')
def currency(*args):
    'dirty float (strip non-numeric characters)'
    if args and isinstance(args[0], str):
        args = [''.join(ch for ch in args[0] if ch in floatchars)]
    return float(*args)


@Column.api
def displayer_currency(col, dw, width=None):
    text = dw.text

    if isinstance(dw.typedval, (int, float)):
        if dw.typedval < 0:
            text = f'({dw.text[1:]})'.rjust(width-1)
            yield ('currency_neg', '')
        else:
            text = text.rjust(width-2)

    yield ('', text)

Sheet.addCommand('$', 'type-currency', 'cursorCol.type=currency; cursorCol.displayer="currency"', 'set type of current column to currency')

vd.addMenuItems('''
    Column > Type as > dirty float > type-currency
''')
