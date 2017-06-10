#!/usr/bin/env python3

'Whitespace Invaders v0.50'

import sys
import requests
import time
import getpass
import hashlib
import builtins

from visidata import *

option('refresh_rate_s', 2.0, 'time to sleep between refreshes')
theme('color_dest_planet', 'underline', 'color of marked destination planet')

command('N', 'status(g_client.get("/regen_map")); g_client.Map.reload()', 'make New map')
command('Y', 'vd.push(g_client.Players).reload()', 'push players sheet')
command('P', 'vd.push(g_client.Planets).reload()', 'push planets sheet')
command('M', 'vd.push(g_client.Map).reload()', 'push map sheet')
command('Q', 'vd.push(g_client.QueuedDeployments)', 'push unsent routes sheet')
command('D', 'vd.push(g_client.HistoricalDeployments).reload()', 'push historical deployments sheet')
command('E', 'vd.push(g_client.Events).reload()', 'push events sheet')
command('^S', 'g_client.QueuedDeployments.submit_deployments()', 'submit deployments and end turn')

options.disp_column_sep = ''

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class WSIClient:
    def __init__(self, url):
        self.sessionid = None
        self.server_url = url

        self.Players = PlayersSheet()
        self.Planets = PlanetsSheet()
        self.QueuedDeployments = QueuedDeploymentsSheet()
        self.Events = EventsSheet()
        self.Map = MapSheet()
        self.HistoricalDeployments = HistoricalDeploymentsSheet()

        vd().rightStatus = self.rightStatus
        self.gamestate = {}
        self.refresh = False

    def rightStatus(self):
        if not self.gamestate:
            self.refresh = True
            g_client.refresh_everything()

        rstatus = '[%s] ' % self.username
        turn_num = self.gamestate.get('current_turn')
        if turn_num:
            rstatus += 'Turn %s' % turn_num
        return rstatus

    def login(self):  # before curses init
        self.username = builtins.input('player name: ')
        password = getpass.getpass('password: ')

        data = { 'username': self.username, 'password': hashlib.md5(password.encode('utf-8')).hexdigest() }

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

    def add_deployment(self, src, dest, nships):
        r = self.get('/validate_deploy', launch_planet_name=src.name, dest_planet_name=dest.name, nships_requested=nships)
        if r.status_code != 200:
            status(r.text)
        else:
            d = AttrDict(r.json())
            d.result = None
            self.QueuedDeployments.rows.append(d)
            status('queued deployment')

    @async
    def refresh_everything(self):
        while True:
            if self.refresh:
                self.gamestate = self.get('/gamestate').json()

                self.Players.reload()
#                self.Planets.reload()
#                self.Events.reload()
#                self.Map.reload()
#                self.HistoricalDeployments.reload()

            time.sleep(options.refresh_rate_s)


class PlayersSheet(Sheet):
    def __init__(self):
        super().__init__('players')

        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('ready'),
        ]
        self.command(ENTER, 'status(g_client.get("/ready").text)', 'Indicate ready to start')

        self.colorizers.append(lambda sheet,col,row,value: row and (row.color, 8))

    def reload(self):
        self.rows = [AttrDict(r) for r in g_client.get('/players').json()]
        self.rows.sort(key=lambda row: row.name)

    def get_player_color(self, playername):
        for plrow in self.rows:
            if plrow.name == playername:
                return plrow.color

def ColumnItems(key_list, **kwargs):
    return [ColumnItem(x, x, **kwargs) for x in key_list]

def ColumnAttrs(key_list, **kwargs):
    return [ColumnAttr(x, **kwargs) for x in key_list]


class PlanetsSheet(Sheet):
    def __init__(self):
        super().__init__('planets')
        self.columns = ColumnAttrs('name x y prod killpct ownername nships'.split())
        self.colorizers.append(lambda sheet,col,row,value: (g_client.Players.get_player_color(row.ownername), 5) if row else None)
        self.colorizers.append(lambda sheet,col,row,value: (options.color_dest_planet, 5) if row is sheet.marked_planet else None)
        self.marked_planet = None

        self.command('m', 'sheet.marked_planet = cursorRow', 'mark current planet as destination')
        self.command('f', 'g_client.add_deployment(cursorRow, marked_planet, int(input("# ships: ")))', 'deploy N ships from current planet to marked planet')

    def reload(self):
        # name, x, y, prod, killpct, owner.name, nships
        self.rows = [AttrDict(x) for x in g_client.get('/planets').json()]
        self.rows.sort(key=lambda row: row.name)


class QueuedDeploymentsSheet(Sheet):
    def __init__(self):
        super().__init__('queued_deployments')

        self.columns = [
            ColumnItem('src_turn', 'launch_turn'),
            ColumnItem('dest_turn', 'launch_turn'),
            ColumnItem('src', 'launch_planet_name'),
            ColumnItem('dest', 'dest_planet_name'),
            ColumnItem('nrequested', 'nships_requested'),
            ColumnItem('ndeployed', 'nships_deployed'),
            ColumnItem('result', 'result'),
        ]

        self.colorizers.append(self.colorIncomplete)

    @staticmethod
    def colorIncomplete(sheet, col, row, value):
        if row and col and col.name == 'ndeployed':
            if row.result and row.nships_deployed != row.nships_requested:
                return 'red bold', 5

    def submit_deployments(self):
        for i, depl in enumerate(self.rows):
            if depl.result:
                continue
            try:
                r = g_client.get('/deploy', **depl)
                self.rows[i] = AttrDict(r.json())
            except Exception as e:
                self.rows[i].result = str(e)

        status(g_client.get('/end_turn').text)

    def reload(self):
        pass


class HistoricalDeploymentsSheet(Sheet):
    def __init__(self):
        super().__init__('deployments')
        self.columns = [
            ColumnItem('player', 'launch_player_name'),
            ColumnItem('src_turn', 'launch_turn'),
            ColumnItem('dest_turn', 'launch_turn'),
            ColumnItem('src', 'launch_planet_name'),
            ColumnItem('dest', 'dest_planet_name'),
            ColumnItem('nships', 'nships_deployed'),
            ColumnItem('killpct', 'nships_deployed'),
        ]

    def reload(self):
        self.rows = g_client.get('/deployments').json()


class EventsSheet(Sheet):
    def __init__(self):
        super().__init__('events')
        self.columns = ColumnItems('turn event'.split())

    def reload(self):
        self.rows = g_client.get('/events').json()


class MapSheet(Sheet):
    def __init__(self):
        super().__init__('map')
        self.colorizers.append(self.colorPlanet)
        self.colorizers.append(self.colorMarkedPlanet)
        self.command('m', 'g_client.Planets.marked_planet = cursorRow[cursorCol.x]', 'mark current planet as destination')
        self.command('f', 'g_client.add_deployment(cursorRow[cursorCol.x], g_client.Planets.marked_planet, int(input("# ships: ")))', 'deploy N ships from current planet to marked planet')

    @staticmethod
    def colorMarkedPlanet(sheet,col,row,value):
        return (options.color_dest_planet, 5) if row and col and row[col.x] and row[col.x] is g_client.Planets.marked_planet else None

    @staticmethod
    def colorPlanet(sheet,col,row,value):
        return (g_client.Players.get_player_color(row[col.x].ownername), 9) if row and col and row[col.x] else None

    def reload(self):
        g_client.Planets.reload()
        map_w = g_client.gamestate['map_width']
        map_h = g_client.gamestate['map_height']

        self.columns = []
        for x in range(map_w):
            c = Column('', width=3, getter=lambda row,x=x: row[x].name if row[x] else '.')
            c.x = x
            self.columns.append(c)

        self.rows = []
        for y in range(map_h):
            current_row = []
            for x in range(map_w):
                current_row.append(None)
            self.rows.append(current_row)

        for planet in g_client.Planets.rows:
            self.rows[planet.y][planet.x] = planet

        # so the order can't be changed
        self.columns = tuple(self.columns)
        self.rows = tuple(self.rows)

g_client = WSIClient(sys.argv[1])

if __name__ == '__main__':
    print(__doc__)
    set_global('g_client', g_client)
    g_client.login()
    run([g_client.Players])

