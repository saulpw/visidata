#!/usr/bin/env python3

import sys
import requests
import time
import getpass
import hashlib
import builtins

from visidata import *

option('refresh_rate_s', 1.0, 'time to sleep between refreshes')
theme('color_dest_planet', 'underline', 'color of marked destination planet')

class WSIClient:
    def __init__(self, url):
        self.sessionid = None
        self.server_url = url

    def login(self):  # before curses init
        username = builtins.input('player name: ')
        password = getpass.getpass('password: ')

        data = { 'username': username, 'password': hashlib.md5(password.encode('utf-8')).hexdigest() }

        r = requests.post(self.server_url + '/auth', data=data)

        if r.status_code == 200:
            self.sessionid = r.text
        else:
            error('[%s] %s' % (r.status_code, r.text))

        try:
            status(self.get('/join').text)
        except Exception as e:
            print(str(e))

    def get(self, path, **kwargs):
        if not self.sessionid:
            error('not logged in')

        kwargs['session'] = self.sessionid

        r = requests.get(self.server_url + path, params=kwargs)

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
command('D', 'vd.push(DeploymentsSheet())', 'push deployment sheet')
command('M', 'vd.push(MapSheet())', 'push map sheet')

class PlanetsSheet(Sheet):
    def __init__(self):
        super().__init__('planets')
        self.columns = ArrayNamedColumns('name x y prod killpct owner nships'.split())
        self.colorizers.append(lambda sheet,col,row,value: (g_players.get_player_color(row[5]), 5) if row else None)
        self.colorizers.append(lambda sheet,col,row,value: (options.color_dest_planet, 5) if row is sheet.marked_planet else None)
        self.marked_planet = None

        self.command('m', 'sheet.marked_planet = cursorRow', 'mark current planet as destination')
        self.command('f', 'status(deploy(cursorRow, marked_planet, int(input("# ships: "))))', 'deploy N ships from current planet to marked planet')

    def reload(self):
        # name, x, y, prod, killpct, owner.name, nships
        self.rows = g_client.get('/planets').json()

    def deploy(self, src, dest, nships):
        return g_client.get('/deploy', launch_planet=src[0], dest_planet=dest[0], nships=nships).text


class DeploymentsSheet(Sheet):
    def __init__(self):
        super().__init__('deployments')
        self.columns = ArrayNamedColumns('launch_player launch_planet dest_planet dest_turn nships killpct'.split())

    def reload(self):
        self.rows = g_client.get('/deployments').json()

class LocalPlanet:
    def __init__(self, row):
        self.name, self.x, self.y, self.prod, self.killpct, self.ownername, self.nships = row

class MapSheet(Sheet):
    def __init__(self):
        super().__init__('map')
        self.colorizers.append(self.colorPlanet)


    @staticmethod
    def colorPlanet(sheet,col,row,value):
        return (g_players.get_player_color(row[col.x].ownername), 9) if row and col and row[col.x] else None

    def reload(self):
        gamestate = g_client.get('/gamestate').json()
        map_w = gamestate['map_width']
        map_h = gamestate['map_height']
        planets = g_client.get('/planets').json()

        self.columns = []
        for x in range(map_w):
            c = Column(str(x), width=3, getter=lambda row,x=x: row[x].name if row[x] else '.')
            c.x = x
            self.columns.append(c)

        self.rows = []
        for y in range(map_h):
            current_row = []
            for x in range(map_w):
                current_row.append(None)
            self.rows.append(current_row)

        for planet in planets:
            lplanet = LocalPlanet(planet)
            self.rows[lplanet.y][lplanet.x] = lplanet


g_players = PlayersSheet()
g_client = WSIClient(sys.argv[1])

vd().rightStatus = lambda: time.strftime('%H:%M:%S')

if __name__ == '__main__':
    g_client.login()
    set_global('g_client', g_client)
    set_global('PlanetsSheet', PlanetsSheet)
    set_global('DeploymentsSheet', DeploymentsSheet)
    set_global('MapSheet', MapSheet)
    run([g_players])

