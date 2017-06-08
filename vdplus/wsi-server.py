#!/usr/bin/env python3

import sys
import json
import http.server
import urllib.parse
import uuid
import random


player_colors = 'green yellow cyan magenta red blue'.split()
planet_names = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
map_width = 10
map_height = 10
rand = random.randrange

class Player:
    def __init__(self, number, name, md5_password, sessionid):
        self.number = number
        self.name = name
        self.md5_password = md5_password
        self.sessionid = sessionid
        self.ready = False

    def as_tuple(self):
        return (self.number, self.name, player_colors[self.number], self.ready)


class Planet:
    def __init__(self, name, x, y, prod, killpct, owner=None):
        self.name = name
        self.x = x
        self.y = y
        self.prod = prod
        self.killpct = killpct
        self.owner = owner
        self.nships = prod

    def as_tuple(self):
        return (self.name, self.x, self.y, self.prod, self.killpct, self.owner, self.nships)

class HTTPException(Exception):
    def __init__(self, errcode, text):
        super().__init__(text)
        self.errcode = errcode

class WSIServer(http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_started = False
        self.players = {}   # [playername] -> Player()
        self.sessions = {}
        self.planets = {}

    def start_game(self):
        self.generate_planets()

    @property
    def started(self):
        return bool(self.planets)

    def generate_planets(self):
        # name, x, y, prod, killpct, owner, nships
        nplayers = len(self.players)
        for i, (name, pl) in enumerate(self.players.items()):
            planet_name = planet_names[i]
            self.planets[name] = Planet(name, rand(map_width), rand(map_height), 10, 40, pl)

        for name in planet_names[nplayers:]:
            self.planets[name] = Planet(name, rand(map_width), rand(map_height), rand(10), rand(40))


class WSIHandler(http.server.BaseHTTPRequestHandler):
    def generic_handler(self, reqtype, path, *args, **kwargs):
        toplevel = path.split('/')[1]
        if toplevel:
            try:
                ret = getattr(self, '%s_%s' % (reqtype, toplevel))(*args, **kwargs)
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                if isinstance(ret, list) or isinstance(ret, dict):
                    ret = json.dumps(ret)

                self.wfile.write(ret.encode('utf-8'))
            except HTTPException as e:
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
        query = urllib.parse.parse_qs(parsed_url.query)
        sessionid = query['session'][0]
        pl = self.server.sessions.get(sessionid)
        if not pl:
            raise HTTPException(403, 'Invalid sessionid')

        self.generic_handler('GET', parsed_url.path, pl, query)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length)
        fields = urllib.parse.parse_qs(field_data)
        fields = dict((k.decode('utf-8'), v) for k, v in fields.items())
        self.generic_handler('POST', self.path, fields)

    def POST_join(self, fields):
        playername = fields['username'][0].decode('utf-8')
        if playername in self.server.players:
            pl = self.server.players[playername]
            if fields['password'][0] == pl.md5_password:
                return pl.sessionid
            else:
                raise HTTPException(403, 'Sorry, wrong password')
        else:
            if self.server.game_started:
                raise HTTPException(403, 'Sorry, game has already started, no new players')
            else:
                sessionid = uuid.uuid1().hex
                pl = Player(len(self.server.players), playername, fields['password'][0], sessionid)
                self.server.players[playername] = pl
                self.server.sessions[sessionid] = pl
                return sessionid

    def GET_ready(self, pl, query):
        pl.ready = True
        if len(self.server.players) > 1 and all(pl.ready for pl in self.server.players.values()):
            self.server.start_game()
            return 'game started'
        return 'ok'

    def GET_players(self, pl, query):
        return [x.as_tuple() for x in self.server.players.values()]

    def GET_planets(self, pl, query):
        return [x.as_tuple() for x in self.server.planets.values()]


def main():
    server = WSIServer(('', 8080), WSIHandler)

    print("http://localhost:8080")
    server.serve_forever()

if __name__ == '__main__':
    main()

