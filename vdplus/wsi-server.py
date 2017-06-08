#!/usr/bin/env python3

import http.server
import urllib.parse
import uuid
import json

planets = [
# name, x, y, prod, killpct, owner, nships
    ['A', 5, 5, 10, 40, None, 10],
    ['B', 15, 15, 10, 40, None, 10],
    ['C', 20, 20, 10, 40, None, 10],
]

# 1st-time /join username md5(password)  -> create player, return sessionid
# 2nd-time ...                           -> compare creds, return new sessionid
#  /other_url sessionid                  -> gets user from sessionid

class MyException(Exception):
    def __init__(self, errcode, text):
        super().__init__(text)
        self.errcode = errcode

class WSIServer(http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_started = False
        self.players = {}
        self.sessions = {}

class WSIHandler(http.server.BaseHTTPRequestHandler):
    def generic_handler(self, reqtype, *args, **kwargs):
        toplevel = self.path.split('/')[1]
        if toplevel:
            try:
                ret = getattr(self, '%s_%s' % (reqtype, toplevel))(*args, **kwargs)
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(json.dumps(ret).encode('utf-8'))
            except MyException as e:
                self.send_response(e.errcode)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            except:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

    def do_GET(self):
        query = urllib.parse.parse_qs(self.path)
        self.generic_handler('GET', query)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length)
        fields = urllib.parse.parse_qs(field_data)
        fields = dict((k.decode('utf-8'), v) for k, v in fields.items())
        self.generic_handler('POST', fields)

    def POST_join(self, fields):
        playername = fields['username'][0]
        if playername in self.server.players:
            md5_password, sessionid = self.server.players[playername]
            if fields['password'][0] == md5_password:
                return sessionid
            else:
                raise MyException(403, 'Sorry, wrong password')
        else:
            if self.server.game_started:
                raise MyException(403, 'Sorry, game has already started, no new players')
            else:
                sessionid = uuid.uuid1().hex
                self.server.players[playername] = (fields['password'][0], sessionid)
                self.server.sessions[sessionid] = playername
                return sessionid

    def GET_planets(self, query):
        return planets

server = WSIServer(('', 8080), WSIHandler)

print("http://localhost:8080")
server.serve_forever()


