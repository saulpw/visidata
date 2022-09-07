'''Provide USD(s) function to convert string like '£300' or '205 AUD' to equivalent US$ as float.
Uses data from fixer.io
'''

from visidata import vd
import functools
import json

vd.option('fixer_key', '', 'API Key for fixer.io')
vd.option('fixer_currency_cache_days', 1, 'Cache days for currency conversions')

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

def currency_rates_json(date='latest', base='USD'):
    url = 'https://api.apilayer.com/fixer/%s?base=%s' % (date, base)
    return vd.urlcache(
        url, 
        days=vd.options.fixer_currency_cache_days, 
        headers={'apikey': vd.options.fixer_key}, 
        http_library='requests'
    ).read_text()

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
    callage = "USD(%s)" % (s)
    for currency_symbol, currency_code in currency_symbols.items():
        if currency_symbol in s:
            amt = float(s.replace(currency_symbol, ''))
            return amt*currency_multiplier(currency_code, 'USD')

    amtstr, currcode = s.split(' ')
    return float(amtstr) * currency_multiplier(currcode, 'USD')

vd.addGlobals(globals())
