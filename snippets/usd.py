# provides USD() function to convert string like '£300' or '205 AUD' to equivalent US$ as float
# uses data from fixer.io
from visidata import diskcache
import functools
import json

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

@diskcache('fixer.io-currency-rates.json', 3600*24)
def currency_rates_json(base='USD', date='latest'):
    import urllib.request
    with urllib.request.urlopen('https://api.fixer.io/%s?base=USD' % date) as fp:
        return fp.read().decode('utf-8')

@functools.lru_cache()
def currency_rates(base='USD'):
    return json.loads(currency_rates_json(base))['rates']

@functools.lru_cache()
def currency_multiplier(src_currency, dest_currency):
    'returns equivalent value in USD for an amt of currency_code'
    if src_currency == 'USD':
        return 1.0
    usd_mult = currency_rates()[src_currency]
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


