#!/usr/bin/env python3

'Galactic Conquest for VisiData'

import sys
import math
import requests
import time
import getpass
import hashlib
import builtins

from visidata import *

option('refresh_rate_s', 2.0, 'time to sleep between refreshes')
option('disp_turn_done', '*', 'symbol to indicate player turn taken')

theme('disp_title', 'RCGameJam S1\'17', 'title on map sheet')
theme('color_dest_planet', 'underline', 'color of marked destination planet')
theme('color_empty_space', '20 blue', 'color of empty space')
theme('color_unowned_planet', 'white', 'color of unowned planet')
theme('disp_empty_space', '.', 'color of empty space')
theme('twinkle_rate', '200', 'neg twinkle')

command('G', 'vd.push(g_client.GameOptions)', 'push game options')
command('N', 'status(g_client.get("/regen_map")); g_client.Map.reload()', 'make New map')
command('Y', 'vd.push(g_client.Players)', 'push players sheet')
command('P', 'vd.push(g_client.Planets)', 'push planets sheet')
command('M', 'vd.push(g_client.Map)', 'push map sheet')
command('U', 'vd.push(g_client.QueuedDeployments)', 'push unsent routes sheet')
command('D', 'vd.push(g_client.HistoricalDeployments)', 'push historical deployments sheet')
command('E', 'vd.push(g_client.Events)', 'push events sheet')
command('R', 'vd.push(SheetList("scores", g_client.get("/scores").json()))', 'push scores sheet')
command('^S', 'g_client.submit_turn()', 'submit deployments and end turn')
command('Q', 'g_client.player_quit(); vd.sheets.clear()', 'quit the game (with confirm)')

options.disp_column_sep = ''
options.curses_timeout = '200'
#options.color_current_row = 'reverse white'

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
        self.GameOptions = GameOptionsSheet()

        vd().rightStatus = self.rightStatus
        self.gamestate = {}
        self.refresh = False

    def submit_turn(self):
        if self.current_turn > 0:
            qd = self.QueuedDeployments
            for i, depl in enumerate(qd.rows):
                if depl.result:
                    continue
                try:
                    r = AttrDict(self.get('/deploy', **depl).json())
                    qd.rows[i] = r
                except Exception as e:
                    qd.rows[i].result = str(e)

            status(self.get('/end_turn').text)
        else:
            status(self.get("/ready").text)

    @property
    def current_turn(self):
        if not self.gamestate:
            self.refresh = True
            g_client.refresh_everything()

        return self.gamestate.get('current_turn')

    def rightStatus(self):
        max_turn = self.gamestate.get('num_turns')
        turn_num = self.current_turn

        rstatus = ''
        if turn_num:
            rstatus += 'Turn %s/%s:' % (turn_num, max_turn)

        for pl in self.Players.rows:
            name = pl.name
            if pl.ready:
                name += options.disp_turn_done
            if pl.name == self.username:
                fmtstr = ' [%s]'
            else:
                fmtstr = ' %s'
            rstatus += fmtstr % name

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

    def player_quit(self):
        yn = input('Are you sure you want to leave the game? (y/N) ')
        if yn[:1].upper() == 'Y':
            status(self.get('/player_quit').text)
        else:
            status('Whew! That was close.')

    def add_deployment(self, sources, dest, nships):
        ndeployments = 0
        for src in sources:
            r = self.get('/validate_deploy', launch_planet_name=src.name, dest_planet_name=dest.name, nships_requested=nships)
            if r.status_code != 200:
                status(r.text)
            else:
                d = AttrDict(r.json())
                d.result = None
                self.QueuedDeployments.rows.append(d)
                ndeployments += 1
                src.nships -= d.nships_requested  # keep track for the player
        status('Queued %s deployments' % ndeployments)

    @async
    def refresh_everything(self):
        while True:
            if self.refresh:
                self.Players.reload()  # to see who has taken their turn

                prev_turn = self.gamestate.get('current_turn', 0)
                self.gamestate = self.get('/gamestate').json()

                current_turn = self.gamestate.get('current_turn', 0)
                if current_turn != prev_turn:
                    self.Planets.reload()
                    self.Events.reload()
                    self.Map.reload()
                    self.HistoricalDeployments.reload()

                    if current_turn > self.gamestate.get('num_turns'):

                        scores = self.get("/scores").json()
                        status('Game over. %s is the winner!' % scores[0]['name'])
                        vd().push(SheetList("scores", scores))

                    elif current_turn > 0:
                        vd().push(self.Events)
                        status('Turn %s started' % current_turn)

            time.sleep(options.refresh_rate_s)


class PlayersSheet(Sheet):
    def __init__(self):
        super().__init__('players')

        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('ready'),
        ]

        self.colorizers.append(lambda sheet,col,row,value: row and (row.color, 8))

    def reload(self):
        self.rows = [AttrDict(r) for r in g_client.get('/players').json()]
        self.rows.sort(key=lambda row: row.name)

    def get_player_color(self, playername):
        for plrow in self.rows:
            if plrow.name == playername:
                return plrow.color
        return options.color_unowned_planet

def ColumnItems(key_list, **kwargs):
    return [ColumnItem(x, x, **kwargs) for x in key_list]

def ColumnAttrs(key_list, **kwargs):
    return [ColumnAttr(x, **kwargs) for x in key_list]

def distance_turns(pl1, pl2):
    if pl1 and pl2:
        return max(int(math.sqrt((pl1.y-pl2.y)**2 + (pl1.x-pl2.x)**2)/2 + 0.5), 1)

class PlanetsSheet(Sheet):
    def __init__(self):
        super().__init__('planets')
        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('prod', type=int),
            ColumnAttr('killpct', type=int, fmtstr='%s%%'),
            ColumnAttr('ownername'),
            ColumnAttr('nships', type=int),
            Column('turns_to_marked', type=int, getter=lambda row: distance_turns(row, self.marked_planet)),
            ColumnAttr('x', type=int, width=4),
            ColumnAttr('y', type=int, width=4),
        ]

        self.colorizers.append(lambda sheet,col,row,value: (g_client.Players.get_player_color(row.ownername), 5) if row else None)
        self.colorizers.append(lambda sheet,col,row,value: (options.color_dest_planet, 5) if row is sheet.marked_planet else None)
        self.marked_planet = None

        self.command(ENTER, 'vd.push(g_client.Map).cursorRowIndex = cursorRow.y; g_client.Map.cursorColIndex = cursorRow.x', 'go to this planet on the map')
        self.command('m', 'sheet.marked_planet = cursorRow', 'mark current planet as destination')
        self.command('f', 'g_client.add_deployment([cursorRow], marked_planet, int(input("# ships: ", value=cursorRow.nships)))', 'deploy N ships from current planet to marked planet')
        self.command('gf', 'g_client.add_deployment(selectedRows, marked_planet, int(input("# ships: ")))', 'deploy N ships from each selected planet to marked planet')

    def reload(self):
        # name, x, y, prod, killpct, owner.name, nships
        self.rows = [AttrDict(x) for x in g_client.get('/planets').json()]
        self.rows.sort(key=lambda row: row.name)


class QueuedDeploymentsSheet(Sheet):
    def __init__(self):
        super().__init__('queued_deployments')

        self.columns = [
            ColumnItem('src_turn', 'launch_turn', type=int),
            ColumnItem('dest_turn', 'dest_turn', type=int),
            ColumnItem('src', 'launch_planet_name'),
            ColumnItem('dest', 'dest_planet_name'),
            ColumnItem('nrequested', 'nships_requested', type=int),
            ColumnItem('ndeployed', 'nships_deployed', type=int),
            ColumnItem('result', 'result'),
        ]

        self.colorizers.append(self.colorIncomplete)

    @staticmethod
    def colorIncomplete(sheet, col, row, value):
        if row and col and col.name == 'ndeployed':
            if row.result and row.nships_deployed != row.nships_requested:
                return 'red bold', 5

    def reload(self):
        pass


class HistoricalDeploymentsSheet(Sheet):
    def __init__(self):
        super().__init__('deployments')
        self.columns = [
            ColumnItem('player', 'launch_player_name'),
            ColumnItem('src_turn', 'launch_turn', type=int),
            ColumnItem('dest_turn', 'dest_turn', type=int),
            ColumnItem('src', 'launch_planet_name'),
            ColumnItem('dest', 'dest_planet_name'),
            ColumnItem('nships', 'nships_deployed', type=int),
            ColumnItem('killpct', 'killpct', type=int, fmtstr='%s%%'),
        ]
        self.colorizers.append(self.colorDeployment)

    @staticmethod
    def colorDeployment(sheet, col, row, value):
        if row:
            return (g_client.Players.get_player_color(row['launch_player_name']), 9)

    def reload(self):
        self.rows = g_client.get('/deployments').json()


class EventsSheet(Sheet):
    def __init__(self):
        super().__init__('events')
        self.columns = [
            ColumnItem('turn', 'turn', type=int),
            ColumnItem('event', 'event', width=80),
        ]

    def reload(self):
        self.rows = g_client.get('/events').json()

        # find first event for the current turn and put the toprow there
        for i, (turn, _) in enumerate(self.rows):
            if turn == g_client.current_turn:
                self.topRowIndex = index
                self.cursorRowIndex = index
                break

class MapSheet(Sheet):
    def __init__(self):
        super().__init__('map')
        self.fieldToShow = [ 'name', 'prod', 'killpct', 'nships' ]
        self.command('m', 'g_client.Planets.marked_planet = cursorRow[cursorCol.x]', 'mark current planet as destination')
        self.command('f', 'g_client.add_deployment([cursorRow[cursorCol.x]], g_client.Planets.marked_planet, int(input("# ships: ", value=cursorRow[cursorCol.x].nships)))', 'deploy N ships from current planet to marked planet')
        self.command(' ', 'cycle_info()', 'cycle the information displayed')

        self.colorizers.append(self.colorOwnedPlanet)
        self.colorizers.append(self.colorRoguePlanet)
        self.colorizers.append(self.colorMarkedPlanet)
        self.colorizers.append(self.colorSpace)


    @property
    def title(self):
        return ''.join(c.name for c in columns)

    @title.setter
    def title(self, value):
        for i in range(self.map_w):
            self.columns[i].name = value[i:i+1]

    @staticmethod
    def colorMarkedPlanet(sheet,col,row,value):
        return (options.color_dest_planet, 5) if row and col and row[col.x] and row[col.x] is g_client.Planets.marked_planet else None

    @staticmethod
    def colorOwnedPlanet(sheet,col,row,value):
        return (g_client.Players.get_player_color(row[col.x].ownername), 9) if row and col and row[col.x] else None

    @staticmethod
    def colorRoguePlanet(sheet,col,row,value):
        return (g_client.Players.get_player_color(row[col.x].ownername), 9) if row and col and row[col.x] else None

    @staticmethod
    def colorSpace(sheet,col,row,value):
        if row and col and row[col.x] is None:
            if row is not sheet.cursorRow:
                r = options.color_empty_space
                if random.randrange(0, int(options.twinkle_rate)) == 0:
                    r = 'cyan bold'
                return (r, 2)

    def cycle_info(self):
        self.fieldToShow = self.fieldToShow[1:] + [self.fieldToShow[0]]
        status('showing "%s"' % self.fieldToShow[0])

    def reload(self):
        g_client.Planets.reload()

        # set columns on every reload, to use current width/height
        self.map_w = g_client.gamestate['map_width']
        self.map_h = g_client.gamestate['map_height']

        self.columns = []
        for x in range(self.map_w):
            c = Column(' ', width=3, getter=lambda row,x=x,self=self: getattr(row[x], self.fieldToShow[0]) or '?' if row[x] else options.disp_empty_space)
            c.x = x
            self.columns.append(c)
        self.title = options.disp_title

        # so the order can't be changed
        self.columns = tuple(self.columns)

        self.rows = []
        for y in range(self.map_h):
            current_row = []
            for x in range(self.map_w):
                current_row.append(None)
            self.rows.append(current_row)

        for planet in g_client.Planets.rows:
            self.rows[planet.y][planet.x] = planet

        self.rows = tuple(self.rows)

class GameOptionsSheet(Sheet):
    def __init__(self):
        super().__init__('game_options')
        self.columns = [
            ColumnItem('option', 0),
            ColumnItem('value', 1),
        ]
        self.command([ENTER, 'e'], 'status(g_client.get("/set_option", option=cursorRow[0], value=editCell(1))); reload()', 'edit game option')

    def reload(self):
        self.rows = list(g_client.get('/options').json().items())


if __name__ == '__main__':
    print(__doc__)

    server_addr = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    server_port = int(sys.argv[2] if len(sys.argv) > 2 else 80)

    g_client = WSIClient('http://%s:%s' % (server_addr, server_port))

    vd()._status = ["'N' to generate new 'M'ap; Ctrl-S when ready to start"]
    set_global('g_client', g_client)
    g_client.login()
    run([g_client.Players])

