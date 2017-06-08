#!/usr/bin/env python3

import sys
import requests
import getpass
import hashlib
import builtins

from visidata import *

class WSIClient:
    def __init__(self, url):
        self.sessionid = None
        self.server_url = url

    def login(self):  # before curses init
        username = builtins.input('player name: ')
        password = getpass.getpass('password: ')

        data = { 'username': username, 'password': hashlib.md5(password.encode('utf-8')).hexdigest() }

        r = requests.post(self.server_url + '/join', data=data)

        if r.status_code == 200:
            self.sessionid = r.text
        else:
            error('[%s] %s' % (r.status_code, r.text))

    def get(self, path):
        if not self.sessionid:
            error('not logged in')

        r = requests.get(self.server_url + path, params={'session':self.sessionid})

        if r.status_code != 200:
            error('[%s] %s' % (r.status_code, r.text))

        return r


class PlayersSheet(Sheet):
    def __init__(self):
        super().__init__('players')

        self.columns = [
            ColumnItem('name', 1),
            ColumnItem('ready', 3),
        ]
        self.command(ENTER, 'status(g_client.get("/ready").text); reload()', 'Indicate ready to start')

        self.colorizers.append(lambda sheet,col,row,value: row and (row[2], 8))

    def reload(self):
        r = g_client.get('/players')
        self.rows = r.json()

g_players = PlayersSheet()
g_client = WSIClient(sys.argv[1])

if __name__ == '__main__':
    g_client.login()
    set_global('g_client', g_client)
    run([g_players])

