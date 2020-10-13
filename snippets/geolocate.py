'geolocate(ip): Fetch geolocation info by IP address from hostip.info service.'

import urllib.request
import functools
import json


@functools.lru_cache(10240)  # should actually cache semi-permanently in visidata_dir
def geolocate(ip):
    url = 'http://api.hostip.info/get_json.php?position=true&ip=' + ip
    with urllib.request.urlopen(url) as fp:
        contents = fp.read().decode('utf-8').strip()
        return json.loads(contents)
