#!/usr/bin/env python3

import sys
import string
import math
import json
import http.server
import urllib.parse
import uuid
import random


player_colors = 'green yellow cyan magenta red blue'.split()
all_planet_names =  string.ascii_uppercase + '0123456789' + '☿♀♂♃♄⛢♅♆⚳⚴⚵' + '+&%$#@![](){}=<>'

rand = random.randrange

def error(s):
    raise HTTPException(300, s)

#### options management
class OptionsObject:
    """Get particular option value from `base_options`."""
    def __init__(self, d):
        self._opts = d
    def __getattr__(self, k):
        return self._opts[k]
    def __setitem__(self, k, v):
        if k not in self._opts:
            raise Exception('no such option "%s"' % k)
        self._opts[k] = v

class Game:
    def __init__(self):
        self.options_dict = {
            'num_planets': 30,
            'num_turns': 20,
            'map_width': 16,
            'map_height': 16,
            'debug': True,
        }
        self.options = OptionsObject(self.options_dict)
        self.players = {}   # [playername] -> Player
        self.planets = {}   # [planetname] -> Planet
        self.deployments = []
        self.events = []
        self.current_turn = 0

        self.generate_planets(use_rc_logo=True)

    def notify(self, eventstr):
        self.events.append(Event(self.current_turn, eventstr))

    def start_game(self):
        self.next_turn()

    def end_turn(self):
        for d in self.deployments:
            if d.dest_turn != self.current_turn+1:
                continue

            if d.dest_planet.owner is d.launch_player:
                d.dest_planet.nships += d.nships_deployed
                self.notify('%s sent %d reinforcements to %s' % (d.launch_player, d.nships_deployed, d.dest_planet.name))
                continue

            # battle time
            attack_strength = float(d.nships_deployed * d.killpct)
            defend_strength = float(d.dest_planet.nships * d.dest_planet.killpct)
            if attack_strength == 0:
                self.notify('inconsequential attack against planet %s by player %s with %s ships (%s killpct)' % (d.dest_planet.name, d.launch_player, d.nships_deployed, d.killpct))
                continue

            ratio = defend_strength / (attack_strength + defend_strength)
            attack_num = random.betavariate(2, 2)
            if attack_num > ratio:
                ships_left = (attack_num-ratio)/(1-ratio)*d.nships_deployed
                d.dest_planet.owner = d.launch_player
                self.notify('planet %s overtaken by %s with %d ships (%d%%) (%d ships remain)' % (d.dest_planet.name, d.launch_player, d.nships_deployed, d.killpct, ships_left))
            else:
                ships_left = (ratio-attack_num)/ratio*d.dest_planet.nships
                self.notify('planet %s held its own against an attack by %s with %d ships (%d%%) (%d ships remain)' % (d.dest_planet.name, d.launch_player, d.nships_deployed, d.killpct, ships_left))

            assert ships_left > 0
            d.dest_planet.nships = int(ships_left+0.5)

        for p in self.planets.values():
            if p.owner:
                p.nships += p.prod

        # TODO: generate random events

        self.next_turn()

    def next_turn(self):
        self.current_turn += 1

        for p in self.players.values():
            p.turn_sent = False

        if self.current_turn > self.options.num_turns:
            scores = self.GET_scores(None)
            self.notify('Game over!')
            self.notify('%s is the winner!' % scores[0]['name'])
        else:
            self.notify('turn %d started' % self.current_turn)

    def GET_scores(self, pl, **kwargs):
        player_scores = {}
        for plname in self.players.keys():
            player_scores[plname] = {
                'name': plname,
                'nplanets': 0,
                'nships': 0
            }

        for planet in self.planets.values():
            if planet.owner:
                player_scores[planet.owner.name]['nplanets'] += 1
                player_scores[planet.owner.name]['nships'] += planet.nships

        return sorted(player_scores.values(), key=lambda r: (r['nplanets'], r['nships']), reverse=True)

    def GET_player_quit(self, pl, **kwargs):
        if pl not in self.players.values():
            error('no such player in game')

        self.players.pop(pl.name)

        for planet in self.planets.values():
            if planet.owner is pl:
                planet.owner = None

        self.notify('Player %s has quit the game.' % pl.name)
        return 'Thanks for playing!'

    @property
    def started(self):
        return self.current_turn > 0

    def POST_options(self, pl, **kwargs):
        if self.started:
            return 'game already started'

        if pl not in self.players.values():
            return 'only players in the game can set the options'

        self.options.update(kwargs)

    def GET_options(self, pl, **kwargs):
        return self.options

    def GET_regen_map(self, pl, use_rc_logo=True, **kwargs):
        if self.started:
            error('game already started')

        self.generate_planets(use_rc_logo=use_rc_logo)

    def GET_gamestate(self, pl, **kwargs):
        return {
            'map_width': self.options.map_width,
            'map_height': self.options.map_height,
            'started': self.started,
            'current_turn': self.current_turn,
            'num_turns': self.options.num_turns,
        }

    # leaky
    def POST_auth(self, pl, **kwargs):
        return pl.sessionid

    def GET_join(self, pl, **kwargs):
        if self.started:
            raise HTTPException(402, 'Game already started')

        if pl.number is not None:
            return 'already player %s/%s' % (pl.number, len(self.players))

        pl.number = len(self.players)
        self.players[pl.name] = pl

        self.generate_planets()
        return 'joined game'

    def GET_ready(self, pl, **kwargs):
        if self.started:
            raise HTTPException(402, 'Game already started')

        if not pl:
            raise HTTPException(403, 'Unauthorized')

        pl.turn_sent = True
        if len(self.players) > 1 and all(pl.turn_sent for pl in self.players.values()):
            self.start_game()
            return 'game started'

        return 'player ready'

    def GET_players(self, pl, **kwargs):
        return [x.as_dict() for x in self.players.values()]

    def GET_planets(self, pl, **kwargs):
        return [x.as_dict() for x in self.planets.values()]

    def GET_deployments(self, pl, **kwargs):
        return [x.as_dict() for x in self.deployments if x.dest_turn <= self.current_turn or x.launch_player is pl]

    def GET_events(self, pl):
        return [x.as_dict() for x in self.events]

    def predeploy(self, launch_player, launch_planet_name=None, dest_planet_name=None, dest_turn=None, nships=0):
        if not self.started:
            error('game not yet started')

        launch_planet = self.planets.get(launch_planet_name) or error('no such planet %s' % launch_planet_name)
        if launch_player is not launch_planet.owner:
            error('player does not own planet')

        dest_planet = self.planets.get(dest_planet_name) or error('no such planet %s' % dest_planet_name)

        turns = int(launch_planet.distance(dest_planet)/2 + 0.5)

        if dest_turn is None:
            dest_turn = 0
        dest_turn = max(int(dest_turn), self.current_turn+turns, self.current_turn+1)

        dobj = Deployment(launch_player, self.current_turn, launch_planet, dest_planet, dest_turn, int(nships), launch_planet.killpct)
        dobj.nships_deployed = min(int(nships), launch_planet.nships)
        return dobj

    def GET_deploy(self, launch_player, launch_planet_name=None, dest_planet_name=None, dest_turn=None, nships_requested=0, **kwargs):
        dobj = self.predeploy(launch_player, launch_planet_name, dest_planet_name, dest_turn, nships_requested)


        assert dobj.launch_planet.nships >= dobj.nships_deployed

        d = dobj.as_dict()

        if dobj.nships_deployed > 0:
            dobj.launch_planet.nships -= dobj.nships_deployed
            self.deployments.append(dobj)
            d['result'] = 'deployed'
        else:
            d['result'] = 'no ships'

        return d

    def GET_validate_deploy(self, launch_player, launch_planet_name=None, dest_planet_name=None, dest_turn=None, nships_requested=0, **kwargs):
        dobj = self.predeploy(launch_player, launch_planet_name, dest_planet_name, dest_turn, nships_requested)
        dobj.nships_deployed = 0  # for client to display correctly before actual deployment
        return dobj.as_dict()

    def GET_end_turn(self, pl):
        if not self.started:
            error('game not yet started')

        pl.turn_sent = True
        num_still_turning = len([p for p in self.players.values() if not p.turn_sent])
        if num_still_turning > 0:
            return 'still waiting on %d players' % num_still_turning
        else:
            return self.end_turn()

    def generate_planets(self, use_rc_logo=True):
        # name, x, y, prod, killpct, owner, nships
        self.planets = {}
        planet_names = all_planet_names[:self.options.num_planets]
        nplayers = len(self.players)
        for i, (name, pl) in enumerate(self.players.items()):
            planet_name = planet_names[i]
            self.planets[planet_name] = Planet(planet_name, rand(self.options.map_width), rand(self.options.map_height), 10, 40, pl)

        for planet_name in planet_names[nplayers:]:
            self.planets[planet_name] = Planet(planet_name, rand(self.options.map_width), rand(self.options.map_height), rand(10), rand(39)+1)


class Player:
    def __init__(self, name, md5_password, sessionid):
        self.number = None
        self.name = name
        self.md5_password = md5_password
        self.sessionid = sessionid
        self.turn_sent = False

    def as_dict(self):
        return dict(number=self.number,
                    name=self.name,
                    color=player_colors[self.number],
                    ready=self.turn_sent)

    def __str__(self):
        return self.name


class Planet:
    def __init__(self, name, x, y, prod, killpct, owner=None):
        self.name = name
        self.x = x
        self.y = y
        self.prod = prod
        self.killpct = killpct
        self.owner = owner
        self.nships = prod

    def distance(self, dest):
        return math.sqrt((self.y-dest.y)**2 + (self.x-dest.x)**2)

    def as_dict(self):
        r = {
                'name': self.name,
                'x': self.x,
                'y': self.y,
        }
        if self.owner:  # if owned by any player, all players can see it
            r.update(prod = self.prod,
                     killpct = self.killpct,
                     ownername = self.owner.name,
                     nships = self.nships)
        else:
            r.update(prod = None,
                     killpct = None,
                     ownername = None,
                     nships = None)

        return r

class Deployment:
    def __init__(self, launch_player, launch_turn, launch_planet, dest_planet, dest_turn, nships, killpct):
        self.launch_player = launch_player
        self.launch_turn = launch_turn
        self.launch_planet = launch_planet
        self.dest_planet = dest_planet
        self.dest_turn = dest_turn
        self.nships_requested = nships
        self.nships_deployed = 0
        self.killpct = killpct

    def as_dict(self):
        return {
            'launch_turn': self.launch_turn,
            'launch_player_name': self.launch_player.name,
            'launch_planet_name': self.launch_planet.name, 
            'dest_planet_name': self.dest_planet.name,
            'dest_turn': int(self.dest_turn),
            'nships_requested': self.nships_requested,
            'nships_deployed': self.nships_deployed,
            'killpct': self.killpct
        }


class Event:
    def __init__(self, turn_num, eventstr):
        self.turn_num = turn_num
        self.eventstr = eventstr

    def as_dict(self):
        return {
            'turn': self.turn_num,
            'event': self.eventstr,
        }


### networking via simple HTTP

class HTTPException(Exception):
    def __init__(self, errcode, text):
        super().__init__(text)
        self.errcode = errcode


class WSIServer(http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = Game()
        self.sessions = {}  # sessionid -> Player
        self.users = {}     # username -> Player


class WSIHandler(http.server.BaseHTTPRequestHandler):
    def generic_handler(self, reqtype, path, data):
        fields = urllib.parse.parse_qs(data)
        if 'params' in fields:
            fields = fields['params']

        fields = dict((k, v[0]) for k, v in fields.items())  # every param is a list; assume only one value for any param

        toplevel = path.split('/')[1]
        if toplevel:
            try:
                sessions = fields.pop('session', None)
                if sessions:
                    pl = self.server.sessions.get(sessions)
                else:
                    pl = None

                if not pl:
                    username = fields.get('username')
                    if username:
                        if username in self.server.users:
                            pl = self.server.users[username]
                            if fields['password'] != pl.md5_password:
                                raise HTTPException(403, 'Sorry, wrong password')
                        else:
                            sessionid = uuid.uuid1().hex
                            pl = Player(username, fields['password'], sessionid)
                            self.server.sessions[sessionid] = pl
                            self.server.users[username] = pl

                ret = getattr(self.server.game, '%s_%s' % (reqtype, toplevel))(pl, **fields)

                if isinstance(ret, list) or isinstance(ret, dict):
                    ret = json.dumps(ret)
                # else leave as string

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()

                if ret:
                    self.wfile.write(ret.encode('utf-8'))
            except HTTPException as e:
                if self.server.game.options.debug:
                    import traceback
                    print(traceback.format_exc())
                self.send_response(e.errcode)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        return self.generic_handler('GET', parsed_url.path, parsed_url.query)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length).decode('utf-8')
        return self.generic_handler('POST', self.path, field_data)


def main():
    server = WSIServer(('', 8080), WSIHandler)

    print('http://localhost:8080')
    server.serve_forever()


if __name__ == '__main__':
    main()

