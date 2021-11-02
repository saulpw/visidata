'''Provide USD(s) function to convert string like '£300' or '205 AUD' to equivalent US$ as float.
Uses data from fixer.io
'''

from visidata import vd
import functools
import json

vd.option('fixer_key', '', 'API Key for fixer.io')

currency_symbols = {
    '$': 'USD',
    '£': 'GBP',
    '₩': 'KRW',
    '€': 'EUR',
    '₪': 'ILS',
    'zł': 'PLN',
    '₽': 'RUB',
    '₫': 'VND',
}

def currency_rates_json(date='latest'):
    url = 'http://data.fixer.io/api/%s?access_key=%s' % (date, vd.options.fixer_key)
    return vd.urlcache(url).read_text()

@functools.lru_cache()
def currency_rates():
    return json.loads(currency_rates_json())['rates']

@functools.lru_cache()
def currency_multiplier(src_currency, dest_currency):
    'returns equivalent value in USD for an amt of currency_code'
    if src_currency == 'USD':
        return 1.0
    eur_usd_mult = currency_rates()['USD']
    eur_src_mult = currency_rates()[src_currency]
    usd_mult = eur_usd_mult/eur_src_mult
    if dest_currency == 'USD':
        return usd_mult
    return usd_mult/currency_rates()[dest_currency]

def USD(s):
    for currency_symbol, currency_code in currency_symbols.items():
        if currency_symbol in s:
            amt = float(s.replace(currency_symbol, ''))
            return amt*currency_multiplier(currency_code, 'USD')

    amtstr, currcode = s.split(' ')
    return float(amtstr) * currency_multiplier(currcode, 'USD')

vd.addGlobals(globals())
