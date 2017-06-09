#!/usr/bin/env python3

import sys
import requests
import time
import getpass
import hashlib
import builtins

from visidata import *

option('refresh_rate_s', 1.0, 'time to sleep between refreshes')

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
            ColumnItem('color', 2),
            ColumnItem('ready', 3),
        ]
        self.command(ENTER, 'status(g_client.get("/ready").text)', 'Indicate ready to start')

        self.colorizers.append(lambda sheet,col,row,value: row and (row[2], 8))

    @async
    def reload(self):
        while True:
            self.rows = g_client.get('/players').json()
            time.sleep(options.refresh_rate_s)

    def get_player_color(self, playername):
        for plrow in self.rows:
            if plrow[1] == playername:
                return plrow[2]


command('P', 'vd.push(PlanetsSheet())', 'push planets sheet')
command('R', 'status(g_client.get("/regen_map")); reload()', 'regenerate map')

class PlanetsSheet(Sheet):
    def __init__(self):
        super().__init__('planets')
        self.columns = ArrayNamedColumns('name x y prod killpct owner nships'.split())
        self.colorizers.append(lambda sheet,col,row,value: (g_players.get_player_color(row[5]), 5) if row else None)

    def reload(self):
        self.rows = g_client.get('/planets').json()

g_players = PlayersSheet()
g_client = WSIClient(sys.argv[1])

vd().rightStatus = lambda: time.strftime('%H:%M:%S')

if __name__ == '__main__':
    g_client.login()
    set_global('g_client', g_client)
    set_global('PlanetsSheet', PlanetsSheet)
    run([g_players])

