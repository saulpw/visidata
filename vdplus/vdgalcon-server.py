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
            'num_planets': 57,
            'num_turns': 20,
            'map_width': 15,
            'map_height': 15,
            'toroidal_map': False,  # if the edges are connected
            'map_generator': 'rclogo_fixed',  # or 'random' or 'rclogo_var'
            'debug': False,
        }
        self.options = OptionsObject(self.options_dict)
        self.players = {}   # [playername] -> Player
        self.planets = {}   # [planetname] -> Planet
        self.deployments = []
        self.events = []
        self.current_turn = 0

        self.generate_planets()

    def generate_planets(self):
        f = globals()['generate_map_' + self.options.map_generator]

        self.planets = f(self.options.map_width,
                         self.options.map_height,
                         self.options.num_planets,
                         self.distance)

        # assign a starting planet for each player
        for i, player in enumerate(self.players.values()):
            starting_planet = self.planets[all_planet_names[i]]
            starting_planet.owner = player
            starting_planet.prod = 10
            starting_planet.nships = 10
            starting_planet.killpct = 40

        for planet in self.planets.values():
            if planet.name not in all_planet_names[:len(self.players)]:
                planet.prod = rand(6) + rand(6)
                planet.killpct = rand(11)+rand(11)+rand(11)+rand(11)+6
                planet.nships = max(planet.prod, 1)

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
                if self.options.debug:
                    self.notify('   from %s' % d.launch_planet)
                continue

            # battle time

            attackers = d.nships_deployed
            defenders = d.dest_planet.nships
            attack_killpct = d.killpct
            defend_killpct = d.dest_planet.killpct

            battle_notice = '%s attacked %s (%s ships at %s%%) with %s ships (%s%%)' % (d.launch_player,
                d.dest_planet,
                defenders,
                defend_killpct,
                attackers,
                attack_killpct)

            round_results = []

            while attackers > 0 and defenders > 0:
                killed_by_attackers = sum(1 for i in range(attackers) if rand(100) <= attack_killpct)
                killed_by_defenders = sum(1 for i in range(defenders) if rand(100) <= defend_killpct)
                if self.options.debug:
                    round_results.append('%s/%s' % (
                        defenders-min(killed_by_attackers, defenders),
                        attackers-min(killed_by_defenders, attackers)))

                attackers -= killed_by_defenders
                defenders -= killed_by_attackers

            if round_results:
                battle_notice += '[%s]' % ','.join(round_results)

            if attackers <= defenders:
                defenders = max(defenders, 0)
                battle_notice += ' and was destroyed, leaving %s ships!' % defenders
                d.dest_planet.nships = defenders
            else:
                attackers = max(attackers, 0)
                battle_notice += ' and seized control with %s ships!' % attackers

                d.dest_planet.owner = d.launch_player
                d.dest_planet.nships = attackers

            self.notify(battle_notice)
            if self.options.debug:
                self.notify('   from %s' % d.launch_planet)

        for p in self.planets.values():
            if p.owner:
                # production
                p.nships += p.prod

                # random planetary events
                if rand(100) < 5:
                    if rand(40) > p.killpct:
                        p.killpct += rand(5)
                        self.notify('Planet %s instituted compulsory opera, killpct improved to %s%%' % (p.name, p.killpct))
                    elif rand(10) > p.prod:
                        p.prod += 1
                        self.notify('Planet %s improved its production to %s' % (p.name, p.prod))
                    elif rand(40) < p.killpct:
                        p.killpct -= rand(5)
                        self.notify('Planet %s legalized dancing, killpct dropped to %s%%' % (p.name, p.killpct))
                    elif rand(10) < p.prod:
                        p.prod -= 1
                        self.notify('Planet %s production decreased to %s%%' % (p.name, p.prod))
                    else:
                        self.GET_deploy(p.owner, p.name, random.choice([x.name for x in self.planets.values() if x.owner is p.owner]), None, p.nships)
                        self.notify('Planet %s revolted against the tyrannical rule of %s!' % (p.name, p.owner))
                        p.owner = None

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
            self.notify('*** Turn %d started' % self.current_turn)

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
        return self.options._opts

    def GET_set_option(self, pl, option='', value=''):
        if self.started:
            return 'options cannot be changed after game start'
        if pl.number is None:
            return 'only a participating player can change a game option'

        self.options[option] = type(getattr(self.options, option))(value)
        return 'options.%s is now %s' % (option, value)

    def GET_regen_map(self, pl, **kwargs):
        if self.started:
            error('game already started')

        self.generate_planets()

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

        turns = int(self.distance(launch_planet, dest_planet)/2 + 0.5)
        turns = max(1, turns)

        if dest_turn is None:
            dest_turn = 0
        dest_turn = max(int(dest_turn), self.current_turn+turns)

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

    def distance(self, here, dest):
        if self.options.toroidal_map:
            # toroidal distance : going off the edge comes back on the other side
            return math.sqrt( ((here.y-dest.y) % self.options.map_height)**2 + ((here.x-dest.x) % self.options.map_width)**2)
        else:
            return math.sqrt((here.y-dest.y)**2 + (here.x-dest.x)**2)


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
    def __init__(self, name, x, y, prod=0, killpct=0, owner=None):
        self.name = name
        self.x = x
        self.y = y
        self.prod = prod
        self.killpct = killpct
        self.owner = owner
        self.nships = prod

    @property
    def xy(self):
        return (self.x, self.y)

    def __str__(self):
        return self.name

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
                self.wfile.write(str(traceback.format_exc()).encode('utf-8')) #
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(traceback.format_exc()).encode('utf-8'))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        return self.generic_handler('GET', parsed_url.path, parsed_url.query)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length).decode('utf-8')
        return self.generic_handler('POST', self.path, field_data)


def generate_map_random(width, height, num_planets, distancefunc):
    planets = {}

    for planet_name in all_planet_names[:num_planets]:
        x = rand(width)
        y = rand(height)
        while (x,y) in planet_coords:
            x = rand(width)
            y = rand(height)

        planets[planet_name] = Planet(planet_name, x, y)
        planet_coords.add((x,y))

    return planets


def generate_map_rclogo_fixed(width, height, num_planets, distancefunc):
    grid = '''
.X.X.X.G.X.X.X.
.X...........X.
....E.X.X......
.X...........X.
.....XX.XB.....
.X...........X.
...............
.C.X.X.H.X.X.D.
......X.X......
..X.X.X.X.X.X..
X.X.........X.X
....X.X.X.F....
X..A.X.X.X....X
...............
X.X.X.X.X.X.X.X'''

    starting_coords = {}
    rclogo_coords = []
    for y, line in enumerate(grid.strip().splitlines()):
        for x, ch in enumerate(line):
            if ch == 'X':
                rclogo_coords.append((x, y))
            elif ch != '.':
                starting_coords[ch] = (x, y)

    random.shuffle(rclogo_coords)

    planets = {}
    for planet_name in all_planet_names[:num_planets]:
        if planet_name in starting_coords:
            x, y = starting_coords[planet_name]
        else:
            x, y = rclogo_coords.pop()

        planets[planet_name] = Planet(planet_name, x, y)

    return planets


def generate_map_rclogo_var(width, height, num_planets, distancefunc):
    planet_names = all_planet_names[:num_planets]

    def allowed_coord_set(width, height):
        def rectangle(leftupper, rightlower): # inclusive
            return set([(i,j) for i in range(leftupper[0], rightlower[0]+1) for j in range(leftupper[1], rightlower[1]+1)])

        allowed = set()

        allowed = allowed | rectangle((2,2)                  ,(width-3,2))
        allowed = allowed | rectangle((2,int(2/3 * height)-2)  ,(width-3,int(2/3 * height)-2))
        allowed = allowed | rectangle((int(6/15 * width),int(2/3 * height)-1),(int(6/15 * width),int(2/3 * height))) # left stand
        allowed = allowed | rectangle((int(7/15 * width),int(2/3 * height)+1), (int(7/15*width), int(2/3 * height)+2)) # right stand
        allowed = allowed | rectangle((int(8/15 * width),int(2/3 * height)-1),(int(8/15 * width),int(2/3 * height))) # left stand
        allowed = allowed | rectangle((int(9/15 * width),int(2/3 * height)+1), (int(9/15*width), int(2/3 * height)+2)) # right stand
        allowed = allowed | rectangle( (int(width*2/10),height-3)        ,(int(3/10*width),height-3)) # left keyboard
        allowed = allowed | rectangle( (int(width*4/10),height-2)        ,(int(5/10*width),height-2)) # left keyboard
        allowed = allowed | rectangle( (int(width*6/10),height-3)        ,(int(7/10*width),height-3)) # left keyboard
        allowed = allowed | rectangle( (int(width*7/10),height-2)        ,(int(8/10*width),height-2)) # right keyboard

        allowed = allowed | rectangle( (2,2)                  ,(2,int(2/3 * height)-2) )  # left edge
        allowed = allowed | rectangle((width-3,2)             ,(width-3,int(2/3 * height)-2))  # right edge
        assert height not in [x[1] for x in allowed], "allowed set is too tall"
        assert width not in [x[0] for x in allowed], "allowed set is too wide"

        return allowed

    def planet_away_from_planets(width, height, existingplanets):
        def min_distance(oneplanet, planets):
            return min(map(lambda x, oneplanet=oneplanet, distancefunc=distancefunc: distancefunc(oneplanet,x), planets))

        def index_best(potentialplanets, ownedplanets):
            distances = map(lambda x, ownedplanets=ownedplanets: min_distance(x ,ownedplanets), potentialplanets)
            index_of_best_planet = max([(d,i) for i,d in enumerate(distances)])[1]
            return index_of_best_planet

        ownedplanets = [p for p in existingplanets.values() if p.owner is not None]
        potentialplanets = random.sample(list(existingplanets.values()),k=5)
        if len(ownedplanets) > 0 :
            idx =  index_best(ownedplanets, potentialplanets)
            return potentialplanets[idx]
        else:
            return potentialplanets[0]

    # body
#    if planets is not None:
#        owners = [p.owner for p in planets.values() if p.owner is not None]
#    else:
#        owners = []

#    owned_planet_coords = set([p.xy for p in planets.values() if p.owner is not None])
    newcoord_list = random.sample(allowed_coord_set(width, height), k=len(planet_names))

    planets = {}
    for i, planet_name in enumerate(planet_names[:num_planets]):
        planets[planet_name] = Planet(planet_name, newcoord_list[i][0], newcoord_list[i][1])

#    for i, (name, pl) in enumerate(self.players.items()):
#        if pl not in owners or planets is None  :
#            planet_name = planet_names[i]
#            (xx,yy) = planet_away_from_planets(width, height, self.planets).xy
#            self.planets[planet_name] = Planet(planet_name, xx, yy, 10, 40, pl)

    return planets


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', dest='port', help='port to run on', default=8080)
    args = parser.parse_args()

    port = int(args.port)

    server = WSIServer(('', port), WSIHandler)

    import requests
    public_ip = requests.get('http://ip.42.pl/raw').text

    print('http://%s:%s' % (public_ip, port))
    server.serve_forever()


if __name__ == '__main__':
    main()

