import json
import threading
import time
import random
import websocket

import requests

from visidata import *

vd.option('rc_app_id', '', 'app id for RC Together')
vd.option('rc_app_secret', '', 'secret key for RC Together')
vd.option('rc_bot_name', 'vdbot', 'default bot name')
vd.option('rc_bot_emoji', '\U0001f9df', 'default emoji for bot')

first_names = '''John Robert William George Charles James David Michael Paul Alexander Richard Joseph Louis Henry Thomas Peter Edward Jean Karl Carl Daniel Philip Alfred Christian Hans Martin Frederick José Johann Carlos Ferdinand Mary Juan Pierre Ivan Albert Giovanni Jan Otto Wilhelm Arthur Max Chris Frank Mikhail Mark Roger Anna Alan Antonio Friedrich Jacques Steve Kim Ernst Fernando Kevin Tom Walter Vladimir Eric Francis Franz Heinrich Nikolai François Andrew Giuseppe Jack Samuel Muhammad Manuel André Brian Boris Claude Stephen Ian Mario Christopher Francisco Georges Maurice Maria Simon Joe Adam Anne Anthony Constantine Elizabeth Georg Henri Jim Kurt Ptolemy Victor Ahmed Patrick Gustav Johannes Marcus Nicolas René Tim Michel Hugo Aaron Anton Bill Mike Diego Gabriel Prince Hermann Jennifer Ben Roberto Rudolf Sergei Sam Jason Viktor Andrei Alfonso Aleksandr Alberto Bernard Billy Catherine Leo Isaac Javier Ludwig Miguel Igor Erich Alessandro Tony Jane Edgar Harold Lee Mohamed Oliver Raymond Steven Sarah Adolf Matthew Pedro Ali Andy Jeff Gary Emil Francesco Guy Howard Herbert Jules Ken Leopold Marco Oscar Ronald Nick Larry Joan Luis Benjamin Bobby Carlo Donald Dennis Edmund Fritz Jorge Justin Julia Konstantin Matt Margaret Marcel Sean Stefan Theodor Maximilian Nicholas Danny Harry Simone Antiochus Omar Andreas Michelle Rafael Johan Ryan Andrea Andrey Ibn Abu Jonathan Felix Julius Jerry'''.split()

ORIGIN_FQHOST = 'recurse.rctogether.com'
BOT_NAME="vdbotlab"
BOT_EMOJI="",  # robot

@VisiData.lazy_property
def vrc(vd):
    return VirtualRC()

color_trans = {
    'orange': '202',
    'light-orange': '214',
    'light-blue': 'cyan',
    'pink': '201',
    'light-pink': '207',
    'purple': 'magenta',
    'light-gray': '252',
    'gray': '244',
}

@VisiData.api
def open_rc(vd, p):
    vd.timeouts_before_idle = -1
    vs = VirtualRCStream(p.name, source=p)
    global ORIGIN_FQHOST
    ORIGIN_FQHOST = p.name + '.rctogether.com'
    vd.rc_api_url = f'https://{ORIGIN_FQHOST}/api'
    vd.vrc.con = Connection(origin=f'https://{ORIGIN_FQHOST}',
                     url=f'wss://{ORIGIN_FQHOST}/cable?app_id={vd.options.rc_app_id}&app_secret={vd.options.rc_app_secret}',
                     identifier={"channel": "ApiChannel"},
                     callback=vs.sub_on_receive)
    vd.vrc.con.connect()
    vd.vrc.streamSheet = vs
    w = VirtualRCWorld(ORIGIN_FQHOST, source=vd.vrc.world)
    w.options.confirm_overwrite = False
    return w

VisiData.new_rc = open_rc

class Connection:
    "The connection to a websocket server"
    def __init__(self, url, origin=None, cookie=None, header=None, identifier=None, callback=None):
        """
        :param url: The url of the cable server.
        :param origin: (Optional) The origin.
        :param cookie: (Optional) A cookie to send (used for authentication for instance).
        :param header: (Optional) custom header for websocket handshake.
        :param identifier: (Optional) identifier for subscription
        """
        self.url = url
        self.origin = origin
        self.cookie = cookie
        self.header = header

        self.websocket = None
        self.ws_thread = None

        self.auto_reconnect = False

        self.identifier = json.dumps(identifier) if identifier else None
        self.receive_callback = callback

    def connect(self):
        if self.connected:
            vd.warning('Connection already established')
            return

        self.auto_reconnect = True

        self.ws_thread = threading.Thread(name="APIConnectionThread", target=self._run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def disconnect(self):
        self.auto_reconnect = False

        if self.websocket:
            self.websocket.close()

    @property
    def connected(self):
        return self.websocket is not None and \
               self.websocket.sock is not None and \
               self.websocket.sock.connected

    def _run_forever(self):
        def _on_message(socket, message):
            vd.debug(f'Data received: {message}')
            data = json.loads(message)
            return getattr(self, 'onmsg_'+data.get('type', 'unknown'))(data)

        def _on_open(socket):
            vd.debug('Connection established')

        def _on_close(socket):
            vd.debug('Connection closed')

        while self.auto_reconnect:
            try:
                self.websocket = websocket.WebSocketApp(
                    self.url,
                    cookie=self.cookie,
                    header=self.header,
                    on_message=_on_message,
                    on_close=_on_close,
                    on_open=_on_open
                )

                self.websocket.run_forever(ping_interval=5, ping_timeout=3, origin=self.origin)

                time.sleep(2)
            except Exception as exc:
                vd.exceptionCaught(exc)

    def send(self, **kwargs):
        vd.debug(f'Send data: {kwargs}')
        assert self.connected, 'Connection not established'
        return self.websocket.send(json.dumps(kwargs, ensure_ascii=False))

    def onmsg_confirm_subscription(self, data):
        pass

    def onmsg_reject_subscription(self, data):
        vd.warning('subscription rejected')

    def onmsg_unknown(self, data):
        if 'message' in data and self.receive_callback:
            return self.receive_callback(data['message'])
        vd.warning(f'Unknown message type '+data['message_type'])

    def onmsg_welcome(self, data):
        self.subscribe()

    def onmsg_ping(self, data):
        pass

    def subscribe(self):
        self.send(command='subscribe', identifier=self.identifier)

    def unsubscribe(self):
        self.send(command='unsubscribe', identifier=self.identifier)

    def send_msg(self, message):
        self.send(command='message', identifier=self.identifier, data=message.raw_message())


class VirtualRC:
    def __init__(self, *args, **kwargs):
        self.bots = {} # botid -> bot info
        self.botResponses = BotResponsesSheet('bot_responses', rows=[])
        self.world = VirtualRCWorldSheet(ORIGIN_FQHOST, rows=[])

    def req(self, method, endpoint, parms={}, **kwargs):
        parms['app_id'] = vd.options.rc_app_id
        parms['app_secret'] = vd.options.rc_app_secret
        parmstr = urllib.parse.urlencode(list(parms.items()))
        r = getattr(requests, method.lower())(url=f"{vd.rc_api_url}/{endpoint}?{parmstr}", json=kwargs)

        self.botResponses.addRow(r)

        if r.status_code != 200:
            vd.warning('%s: %s' % (r.status_code, r.reason))

        return AttrDict(r.json())

    def post(self, endpoint, parms={}, **kwargs):
        return self.req('POST', endpoint, parms=parms, **kwargs)

    @asyncthread
    def delete(self, endpoint, parms={}):
        return self.req('DELETE', endpoint, parms=parms)

    @asyncthread
    def patch(self, endpoint, parms={}, **kwargs):
        return self.req('PATCH', endpoint, parms=parms, **kwargs)

    @property
    def botid(self):
        return list(self.bots.values())[0]['id']

    def add_bots(self, n=1, x=0, y=0):
        for i in range(n):
            self.add_bot(x, y, name=random.choice(first_names))

    @asyncthread
    def add_bot(self, x=0, y=0, name=None, emoji=None):
      with Progress(total=1) as prog:
        r = self.post('bots', bot={
                "name": name or vd.options.rc_bot_name,
                "emoji": emoji or vd.options.rc_bot_emoji,
                "x": x,
                "y": y,
                "direction": "right",
                "can_be_mentioned": False,
            })
        if r:
            vd.vrc.world.addRow(r)

            # update bot message
            self.patch(f'bots/{r.id}', message='bot lab')
        prog.addProgress(1)

class VirtualRCSheet(BaseSheet):
    pass

class BotResponsesSheet(TableSheet, VirtualRCSheet):
    rowtype='bot infos'
    columns=[
        AttrColumn('request.method'),
        AttrColumn('request.path_url'),
        AttrColumn('request.body'),
        AttrColumn('status_code'),
        AttrColumn('reason'),
        Column('content', getter=lambda c,r: r.json()),
    ]

class VirtualRCWorld(TextCanvas, VirtualRCSheet):
    def draw(self, scr):
        super().draw(scr)

        ymax, xmax = scr.getmaxyx()
        for r in self.source.rows:
            if not r.pos: continue
            x, y = r.pos.x, r.pos.y
            if y is None or y < 0 or y > self.windowHeight-2: continue
            if x is None or x < 0 or x > self.windowWidth-1: continue
            try:
                c = colors.color_selected_row if self.source.isSelected(r) else colors[color_trans.get(r.color, r.color)]
                if self.cursorBox.contains(CharBox(None, x, y, 1, 1)):
                    c |= curses.A_REVERSE
                scr.addstr(y, x, r.type[0], c)
            except Exception as e:
                vd.exceptionCaught(e)

    def checkCursor(self):
        self.cursorBox.x1 = min(self.windowWidth-2, max(0, self.cursorBox.x1))
        self.cursorBox.y1 = min(self.windowHeight-2, max(0, self.cursorBox.y1))

    def slide(self, rows, dx, dy):
        super().slide(rows, dx, dy)
        self.source.commit()


class VirtualRCWorldSheet(VirtualRCSheet, TableSheet):
    defer = True
    rowtype='entities'  # rowdef: inner dict from JSON response
    columns=[
        ItemColumn('id', 'id', width=0),
        ItemColumn('type', 'type'),
        ItemColumn('x', 'pos.x', type=int),
        ItemColumn('y', 'pos.y', type=int),
        ItemColumn('direction'),
        ItemColumn('color'),
        ItemColumn('person_name'),
        ItemColumn('owner.name'),
        ItemColumn('app.name'),
        ItemColumn('name', width=0),
        ItemColumn('display_name'),
        ItemColumn('zoom_user.id', width=0),
        ItemColumn('zoom_user.display_name', width=0),
        ItemColumn('participant_count', width=0),
        ItemColumn('width', type=int),
        ItemColumn('height', type=int),
        ItemColumn('has_audio_block', width=0),
        ItemColumn('mute_on_entry', width=0),
        ItemColumn('wall_text'),
        ItemColumn('note_text'),
        ItemColumn('updated_by.name'),
        ItemColumn('updated_by.id', width=0),
        ItemColumn('expires_at', type=date),
        ItemColumn('note_updated_at', type=date),
        ItemColumn('muted', width=0),
        ItemColumn('updated_at', type=date),
        ItemColumn('image_path', width=0),
        ItemColumn('user_id', width=0),
        ItemColumn('last_present_at', width=0),
        ItemColumn('last_idle_at', width=0),
        ItemColumn('zoom_user_display_name', width=0),
        ItemColumn('zoom_meeting_topic', width=0),
        ItemColumn('message.text'),
        ItemColumn('message.sent_at', type=date),
        ItemColumn('message.mentioned_entity_ids', width=0),
        ItemColumn('calendar_data', width=0),
        ItemColumn('emoji'),
        ItemColumn('status'),
        ItemColumn('profile_url', width=0),
        ItemColumn('owner.id', width=0),
        ItemColumn('owner.image_url', width=0),
        ItemColumn('url', width=0),
        ItemColumn('can_be_mentioned', width=0),
        ItemColumn('app.id', width=0),
        ItemColumn('audio_room_id', width=0),
    ]

    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()

        for r, rowmods in Progress(mods.values()):
            t = r.type.lower()
            vd.vrc.patch(f"{t}s/{r.id}", **{c.name:v for c,v in rowmods.items()})

        for r in Progress(dels.values()):
            t = r.type.lower()
            vd.vrc.delete(f"{t}s/{r.id}")

        self.preloadHook()
        self.reload()

    def addRow(self, r, **kwargs):
        r = AttrDict(r)
        if r.type == 'Bot' and r.name == BOT_NAME:
            vd.vrc.bots[r.id] = r

        return super().addRow(r, **kwargs)

    def reload(self):
        self.rows = []
        vd.vrc.con.disconnect()
        vd.vrc.con.connect()

class VirtualRCStream(TableSheet, VirtualRCSheet):
    rowtype='entity updates'  # rowdef: AttrDict of payload from JSON update
    columns=[
        ItemColumn('user', 'person_name'),
        ItemColumn('id', 'id', width=0),
        ItemColumn('type', 'type'),
        ItemColumn('x', 'pos.x', type=int),
        ItemColumn('y', 'pos.y', type=int),
        ItemColumn('dir', 'direction'),
        ItemColumn('muted', 'muted'),
        ItemColumn('updated_at', 'updated_at', type=date, fmtstr='%H:%M'),
        ItemColumn('image_path', width=0),
        ItemColumn('user_id', 'user_id', width=0),
        ItemColumn('last_present', 'last_present_at', width=0, fmtstr='%H:%M'),
        ItemColumn('last_idle', 'last_idle_at', width=0, fmtstr='%H:%M'),
        ItemColumn('zoom_user_display_name', width=0),
        ItemColumn('zoom_meeting_topic', width=0),
        ItemColumn('msg', 'message.text'),
        ItemColumn('msg_sent', 'message.sent_at', type=date),
        ItemColumn('message.mentioned_entity_ids', type=vlen, width=0),
    ]

    def send_msg(self, msg):
        vd.vrc.post('messages', bot_id=vd.vrc.botid, text=msg)

    def delete_bot(self):
        vd.vrc.delete(f'bots/{vd.vrc.botid}')

    def sub_on_receive(self, msg):
        msg = AttrDict(msg)
        if msg.type == "world":
            vd.vrc.world_msg = msg
            vd.vrc.rows = msg.payload.rows
            vd.vrc.cols = msg.payload.cols

            for r in msg.payload.entities:
                vd.vrc.world.addRow(r)

        elif msg.type == 'entity':  # update
            self.addRow(msg.payload)

            for i, r in enumerate(vd.vrc.world.rows):
                if r.id == msg.payload.id:
                    vd.vrc.world.rows[i].update(msg.payload)
                    return

            # wasn't there before
            vd.vrc.world.addRow(msg.payload)
        else:
            vd.warning('unknown msg type "%s"' % msg['type'])

VirtualRCSheet.addCommand('', 'open-rc-msgs', 'vd.push(vd.vrc.botResponses)')
VirtualRCSheet.addCommand('', 'open-rc-stream', 'vd.push(vd.vrc.streamSheet)')

VirtualRCSheet.addCommand('`', 'open-backing', 'vd.push(vd.vrc.world)')
VirtualRCWorldSheet.addCommand('`', 'open-world', 'vd.push(source)')


VirtualRCSheet.addCommand('a', 'add-msg', 'send_msg(input("message: "))')
#VirtualRCWorld.addCommand('w', 'add-wall', 'vrc.post("walls", {"bot_id":vd.vrc.botid}, pos=dict(x=cursorBox.x1, y=cursorBox.y1), color="yellow", wall_text="F")', 'add wall at cursor')
#VirtualRCWorld.addCommand('n', 'add-note', 'vrc.post("notes", {"bot_id":vd.vrc.botid}, pos=dict(x=cursorBox.x1, y=cursorBox.y1), color="yellow", wall_text="F")', 'add note at cursor')
VirtualRCWorld.addCommand('b', 'add-bot', 'vrc.add_bots(1, cursorBox.x1, cursorBox.y1)', 'add bot at cursor')
VirtualRCWorld.addCommand('gb', 'add-bots', 'vrc.add_bots(int(input("# bots to create: ")), cursorBox.x1, cursorBox.y1)', 'add bots at cursor')
