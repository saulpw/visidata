#!/usr/bin/env python3

'Galactic Conquest for VisiData'

import sys
import math
import requests
import time
import getpass
import hashlib
import builtins
import random

from visidata import *

option('refresh_rate_s', 2.0, 'time to sleep between refreshes')
option('disp_turn_done', '*', 'symbol to indicate player turn taken')

theme('disp_title', 'Galactic Conquest', 'title on map sheet')
theme('color_incomplete_deploy', 'red bold', 'color of unresolved deployments')
theme('color_dest_planet', 'underline', 'color of marked destination planet')
theme('color_empty_space', '20 blue', 'color of empty space')
theme('color_unowned_planet', 'white', 'color of unowned planet')
theme('disp_empty_space', '.', 'color of empty space')
theme('twinkle_rate', '200', 'neg twinkle')
theme('color_twinkle', 'cyan bold', 'color of twinkling star')


@VisiData.api
def openhttp_galcon(vd, p):
    vd.g_client = WSIClient(p.given)

    vd._status = ["'N' to generate new 'M'ap; Ctrl+S when ready to start"]

    vd.g_client.login()
    return vd.g_client.Players


class GalconSheet(Sheet):
    pass

GalconSheet.addCommand(ALT+'g', 'options-galcon', 'vd.push(g_client.GameOptions)', 'push game options')
GalconSheet.addCommand(ALT+'n', 'new-map', 'vd.status(g_client.get("/regen_map")); g_client.Map.reload()', 'make New map')
GalconSheet.addCommand(ALT+'y', 'open-players', 'vd.push(g_client.Players)', 'push players sheet')
GalconSheet.addCommand(ALT+'p', 'open-planets', 'vd.push(g_client.Planets)', 'push planets sheet')
GalconSheet.addCommand(ALT+'m', 'open-map', 'vd.push(g_client.Map)', 'push map sheet')
GalconSheet.addCommand(ALT+'u', 'open-routes', 'vd.push(g_client.QueuedDeployments)', 'push unsent routes sheet')
GalconSheet.addCommand(ALT+'d', 'open-deployments', 'vd.push(g_client.HistoricalDeployments)', 'push historical deployments sheet')
GalconSheet.addCommand(ALT+'e', 'open-events', 'vd.push(g_client.Events)', 'push events sheet')
GalconSheet.addCommand(ALT+'r', 'open-scores', 'vd.push(SheetList("scores", g_client.get("/scores").json()))', 'push scores sheet')
GalconSheet.addCommand('^S', 'end-turn', 'g_client.submit_turn()', 'submit deployments and end turn')
GalconSheet.addCommand(ALT+'q', 'quit-game', 'g_client.player_quit(); vd.quit(s for s in vd.sheets if isinstance(s, GalconSheet))', 'quit the game (with confirm)')


class WSIClient:
    def __init__(self, url):
        self.sessionid = None
        self.server_url = url

        self.Players = PlayersSheet('players')
        self.Planets = PlanetsSheet('planets')
        self.QueuedDeployments = QueuedDeploymentsSheet('queued_deployments', rows=[])
        self.Events = EventsSheet('events')
        self.Map = MapSheet('map')
        self.HistoricalDeployments = HistoricalDeploymentsSheet('deployments')
        self.GameOptions = GameOptionsSheet('game_options')

        vd.rightStatus = self.rightStatus
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
            vd.g_client.refresh_everything()

        return self.gamestate.get('current_turn')

    def rightStatus(self, sheet):
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
            error('[login error %s] %s' % (r.status_code, r.text))

        try:
            status(self.get('/join').text)
        except Exception as e:
            print(str(e))

    def get(self, path, **kwargs):
        if not self.sessionid:
            fail('not logged in')

        kwargs['session'] = self.sessionid

        r = requests.get(self.server_url + path, params=kwargs)

        if r.status_code != 200:
            fail(r.text)

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
                self.QueuedDeployments.addRow(d)
                ndeployments += 1
                src.nships -= d.nships_requested  # keep track for the player
        status('Queued %s deployments' % ndeployments)

    @asyncthread
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
                        vd.push(SheetList("scores", scores))

                    elif current_turn > 0:
                        vd.push(self.Events)
                        status('Turn %s started' % current_turn)

            time.sleep(options.refresh_rate_s)


class PlayersSheet(GalconSheet):
    columns = [
        ColumnAttr('name'),
        ColumnAttr('ready'),
    ]
    colorizers = [
        RowColorizer(8, None, lambda s,c,r,v: r and r.color)
    ]

    def loader(self):
        self.rows = []
        for r in vd.g_client.get('/players').json():
            self.addRow(AttrDict(r))

        self.rows.sort(key=lambda row: row.name)

    def get_player_color(self, playername):
        for plrow in self.rows:
            if plrow.name == playername:
                return plrow.color
        return 'color_unowned_planet'


def distance_turns(pl1, pl2):
    if pl1 and pl2:
        return max(int(math.sqrt((pl1.y-pl2.y)**2 + (pl1.x-pl2.x)**2)/2 + 0.5), 1)


class PlanetsSheet(GalconSheet):
    columns = [
        ColumnAttr('name'),
        ColumnAttr('prod', type=int),
        ColumnAttr('killpct', type=int, fmtstr='%s%%'),
        ColumnAttr('ownername'),
        ColumnAttr('nships', type=int),
        Column('turns_to_marked', type=int, getter=lambda col,row: distance_turns(row, col.sheet.marked_planet)),
        ColumnAttr('x', type=int, width=4),
        ColumnAttr('y', type=int, width=4),
    ]

    colorizers = [
        RowColorizer(5, None, lambda sheet,col,row,value: row and vd.g_client.Players.get_player_color(row.ownername)),
        RowColorizer(5, 'color_dest_planet', lambda sheet,c,row,v: row is sheet.marked_planet),
    ]
    marked_planet = None

    def reload(self):
        # name, x, y, prod, killpct, owner.name, nships
        self.rows = []
        for planetobj in vd.g_client.get('/planets').json():
                self.addRow(AttrDict(planetobj))
        self.rows.sort(key=lambda row: row.name)

PlanetsSheet.addCommand(ENTER, 'dive-planet', 'vd.push(g_client.Map); g_client.Map.cursorRowIndex = cursorRow.y; g_client.Map.cursorColIndex = cursorRow.x', 'go to this planet on the map')
PlanetsSheet.addCommand('m', 'mark-planet', 'sheet.marked_planet = cursorRow', 'mark current planet as destination')
PlanetsSheet.addCommand('f', 'deploy-planet', 'g_client.add_deployment([cursorRow], marked_planet, int(input("# ships: ", value=cursorRow.nships)))', 'deploy N ships from current planet to marked planet')
PlanetsSheet.addCommand('gf', 'deploy-planets-selected', 'g_client.add_deployment(selectedRows, marked_planet, int(input("# ships: ")))', 'deploy N ships from each selected planet to marked planet')


class QueuedDeploymentsSheet(GalconSheet):
    columns = [
        ColumnItem('src_turn', 'launch_turn', type=int),
        ColumnItem('dest_turn', 'dest_turn', type=int),
        ColumnItem('src', 'launch_planet_name'),
        ColumnItem('dest', 'dest_planet_name'),
        ColumnItem('nrequested', 'nships_requested', type=int),
        ColumnItem('ndeployed', 'nships_deployed', type=int),
        ColumnItem('result', 'result'),
    ]
    colorizers = [
            CellColorizer(5, 'red bold', lambda s,c,r,v: c and s.colorIncomplete(c,r,v))
    ]

    def colorIncomplete(self, col, row, value):
        if row and col.name == 'ndeployed':
            if row.result and row.nships_deployed != row.nships_requested:
                return 'red bold'

    def reload(self):
        self.rows = []


class HistoricalDeploymentsSheet(GalconSheet):
    columns = [
        ColumnItem('player', 'launch_player_name'),
        ColumnItem('src_turn', 'launch_turn', type=int),
        ColumnItem('dest_turn', 'dest_turn', type=int),
        ColumnItem('src', 'launch_planet_name'),
        ColumnItem('dest', 'dest_planet_name'),
        ColumnItem('nships', 'nships_deployed', type=int),
        ColumnItem('killpct', 'killpct', type=int, fmtstr='%s%%'),
    ]
    colorizers = [
        RowColorizer(9, None, lambda s,c,r,v: r and vd.g_client.Players.get_player_color(r['launch_player_name']))
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        for r in vd.g_client.get('/deployments').json():
            self.addRow(r)


class EventsSheet(GalconSheet):
    columns = [
        ColumnItem('turn', 'turn', type=int),
        ColumnItem('event', 'event', width=80),
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        for row in vd.g_client.get('/events').json():
            self.addRow(row)

        # find first event for the current turn and put the toprow there
        for i, (turn, _) in enumerate(self.rows):
            if turn == vd.g_client.current_turn:
                self.topRowIndex = index
                self.cursorRowIndex = index
                break

def CellColor(prec, color, func):
    return CellColorizer(prec, color, lambda s,c,r,v,f=func: r and c and f(s,c,r,v))


class MapSheet(GalconSheet):
    fieldToShow = [ 'name', 'prod', 'killpct', 'nships' ]

    colorizers = [
        CellColor(9, None, lambda s,c,r,v: vd.g_client.Players.get_player_color(r[c.x].ownername) if r[c.x] else None),
        CellColor(5, 'color_dest_planet', lambda s,c,r,v: r[c.x] and r[c.x] is vd.g_client.Planets.marked_planet),
        CellColor(2, None, lambda s,c,r,v: s.colorSpace(c,r,v)),
    ]

    @property
    def title(self):
        return ''.join(c.name for c in columns)

    @title.setter
    def title(self, value):
        for i in range(self.map_w):
            self.columns[i].name = value[i:i+1]

    def colorSpace(sheet,col,row,value):
        if row and col and row[col.x] is None:
            if row is not sheet.cursorRow:
                r = options.color_empty_space
                if random.randrange(0, int(options.twinkle_rate)) == 0:
                    r = 'cyan bold'
                return r

    def cycle_info(self):
        self.fieldToShow = self.fieldToShow[1:] + [self.fieldToShow[0]]
        status('showing "%s"' % self.fieldToShow[0])

    def reload(self):
        vd.g_client.Planets.reload()

        # set columns on every reload, to use current width/height
        self.map_w = vd.g_client.gamestate['map_width']
        self.map_h = vd.g_client.gamestate['map_height']

        self.columns = []
        for x in range(self.map_w):
            c = Column(' ', width=3, x=x, getter=lambda col,row: getattr(row[col.x], col.sheet.fieldToShow[0]) or '?' if row[col.x] else options.disp_empty_space)
            self.addColumn(c)
        self.title = options.disp_title

        self.rows = []
        for y in range(self.map_h):
            current_row = []
            for x in range(self.map_w):
                current_row.append(None)
            self.addRow(current_row)

        for planet in vd.g_client.Planets.rows:
            self.rows[planet.y][planet.x] = planet

        # so the order can't be changed
        self.columns = tuple(self.columns)
        self.rows = tuple(self.rows)


MapSheet.addCommand('m', 'mark-planet', 'g_client.Planets.marked_planet = cursorRow[cursorCol.x]', 'mark current planet as destination')
MapSheet.addCommand('f', 'deploy-planet', 'g_client.add_deployment([cursorRow[cursorCol.x]], g_client.Planets.marked_planet, int(input("# ships: ", value=cursorRow[cursorCol.x].nships)))', 'deploy N ships from current planet to marked planet')
MapSheet.addCommand('v', 'cycle-info', 'cycle_info()', 'cycle the information displayed')


class GameOptionsSheet(GalconSheet):
    columns = [
        ColumnItem('option', 0),
        ColumnItem('value', 1),
    ]

    def reload(self):
        self.rows = []
        for r in vd.g_client.get('/options').json().items():
            self.addRow(r)

PlanetsSheet.class_options.disp_column_sep = ''
#PlanetsSheet.class_options.color_current_row = 'reverse white'

GameOptionsSheet.addCommand('e', 'edit-option', 'status(g_client.get("/set_option", option=cursorRow[0], value=editCell(1))); reload()', 'edit game option')
