'''Provide USD(s) function to convert string like '£300' or '205 AUD' to equivalent US$ as float.
Uses data from fixer.io
'''

from visidata import vd
import functools
import json

import logging
logging.basicConfig(filename='/tmp/visidata.log', level=logging.DEBUG)

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

def currency_rates_json(date='latest', base='USD'):
    url = 'https://api.apilayer.com/fixer/%s?base=%s' % (date, base)
    logging.info("currency_rates url=%s" % (url,))
    payload = vd.urlcache(url, days=0, headers={'apikey': vd.options.fixer_key}, http_library='requests').read_text()
    logging.info("currency_rates_json [url=%s] payload %s" % (url, payload))
    return payload

@functools.lru_cache()
def currency_rates():
    rates = json.loads(currency_rates_json())['rates']
    logging.info("currency_rates %s" % (rates, ))
    return rates

@functools.lru_cache()
def currency_multiplier(src_currency, dest_currency):
    'returns equivalent value in USD for an amt of currency_code'
    callage = "currency_multiplier(%s, %s" % (src_currency, dest_currency)
    if src_currency == 'USD':
        logging.info("%s = 1.0 [src_currency 'USD']" % (callage,))
        return 1.0
    eur_usd_mult = currency_rates()['USD']
    eur_src_mult = currency_rates()[src_currency]
    usd_mult = eur_usd_mult/eur_src_mult
    if dest_currency == 'USD':
        logging.info("%s = %s [dst_currency 'USD']" % (callage,usd_mult))
        return usd_mult
    
    calculated = usd_mult/currency_rates()[dest_currency]
    logging.info("%s = %s [calculated]" % (callage,calculated))
    return calculated

def USD(s):
    callage = "USD(%s)" % (s)
    for currency_symbol, currency_code in currency_symbols.items():
        if currency_symbol in s:
            amt = float(s.replace(currency_symbol, ''))
            result = amt*currency_multiplier(currency_code, 'USD')
            logging.info("%s = %s [amt=%s]" % (callage, result, amt))
            return result

    amtstr, currcode = s.split(' ')
    result = float(amtstr) * currency_multiplier(currcode, 'USD')
    logging.info("%s = %s [amtstr=%s, currcode=%s]" % (callage, result, amtstr, currcode))
    return result

vd.addGlobals(globals())
