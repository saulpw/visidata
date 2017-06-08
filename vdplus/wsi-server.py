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

class WSIServer(http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_started = False
        self.players = {}
        self.sessions = {}

class WSIHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/join':
            length = int(self.headers['content-length'])
            field_data = self.rfile.read(length)
            fields = urllib.parse.parse_qs(field_data)
            playername = fields[b'username'][0]
            if playername in self.server.players:
                md5_password, sessionid = self.server.players[playername]
                if fields[b'password'][0] == md5_password:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(sessionid.encode('utf-8'))
                else:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(('Sorry, wrong password').encode('utf-8'))
            else:
                if self.server.game_started:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(('Sorry, game has already started, no new players').encode('utf-8'))
                else:
                    sessionid = uuid.uuid1().hex
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.server.players[playername] = (fields[b'password'][0], sessionid)
                    self.server.sessions[sessionid] = playername
                    self.wfile.write(sessionid.encode('utf-8'))



    def do_GET(self):
        toplevel = self.path.split('/')[1]
        if toplevel:
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            query = urllib.parse.parse_qs(self.path)
            ret = getattr(self, 'GET_' + toplevel)(query)
            self.wfile.write(json.dumps(ret).encode('utf-8'))

    def GET_planets(self, query):
        return planets

server = WSIServer(('', 8080), WSIHandler)

print("http://localhost:8080")
server.serve_forever()


