'''Provide USD(s) function to convert string like '£300' or '205 AUD' to equivalent US$ as float.
Uses data from api.apilayer.com/fixer. Requires an API key for apilayer.com.
'''

from visidata import vd
import functools
import json

vd.option('fixer_api_key', '', 'API Key for api.apilayer.com/fixer')
vd.option('fixer_cache_days', 1, 'Cache days for currency conversions')

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
        days=vd.options.fixer_cache_days,
        headers={
            # First need to set some additional headers as otherwise apilayers will block it with a 403
            # See also https://stackoverflow.com/questions/13303449/urllib2-httperror-http-error-403-forbidden
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',

            # Finally set Apikey
            'apikey': vd.options.fixer_api_key
        }
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
    for currency_symbol, currency_code in currency_symbols.items():
        if currency_symbol in s:
            amt = float(s.replace(currency_symbol, ''))
            return amt*currency_multiplier(currency_code, 'USD')

    amtstr, currcode = s.split(' ')
    return float(amtstr) * currency_multiplier(currcode, 'USD')


vd.addGlobals(USD=USD)
