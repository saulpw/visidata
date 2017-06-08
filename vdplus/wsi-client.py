#!/usr/bin/env python3

import sys
import requests
import getpass
import hashlib

import visidata

game_url = sys.argv[1]

username = input('player name: ')
password = getpass.getpass('password: ')

session = requests.Session()
data = { 'username': username, 'password': hashlib.md5(password.encode('utf-8')).hexdigest() }

r = session.post(game_url + '/join', data=data)

if r.status_code == 200:
    sessionid = r.text
    r = session.get(game_url + '/planets', data={'session':sessionid})
    print(r.text)
else:
    status('[%s] %s' % (r.status_code, r.text))


#visidata.run()
