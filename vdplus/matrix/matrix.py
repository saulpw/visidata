import builtins

from visidata import vd, VisiData, Sheet, Column, ItemColumn, date
from visidata import *

vd.option('matrix_token', '', 'matrix API token')
vd.option('matrix_user_id', '', 'matrix user ID associated with token')
vd.option('matrix_device_id', 'VisiData', 'device ID associated with matrix login')


@VisiData.api
def openhttp_matrix(vd, p):
    if not vd.options.matrix_token:
        import getpass
        from matrix_client.client import MatrixClient

        username = builtins.input(f'{p.given} username: ')
        password = getpass.getpass('password: ')

        vd.matrix_client = MatrixClient(p.given)
        vd.options.matrix_token = vd.matrix_client.login(username, password,
                                                    device_id=vd.options.matrix_device_id)
        with open(str(Path(vd.options.config)), mode='a') as fp:
            fp.write(f'options.matrix_token="{vd.options.matrix_token}"\n')

    vd.timeouts_before_idle = -1
    return MatrixSheet(p.name, source=p)


class MatrixRoomsSheet(Sheet):
    def iterload(self):
        yield from vd.matrix_client.get_rooms().values()


class MatrixSheet(Sheet):
    columns = [
        Column('room', getter=lambda c,r: r.room.display_name),
        ItemColumn('sender', width=10),
        ItemColumn('type', width=0),
        Column('timestamp', width=16, type=date, getter=lambda c,r: r and r.origin_server_ts/1000, fmtstr='%Y-%m-%d %H:%m'),
        ItemColumn('content', width=0),
        ItemColumn('content.body', width=40),
        ItemColumn('received', type=vlen, width=0),
        ItemColumn('content.msgtype'),
    ]

    @asyncthread
    def reload(self):
        from matrix_client.client import MatrixClient
        vd.matrix_client = MatrixClient(self.source.given,
                                        token=self.options.matrix_token,
                                        user_id=self.options.matrix_user_id)

        for room in vd.matrix_client.get_rooms().values():
            self.add_room(room)

        vd.matrix_client.add_listener(self.global_event)
        vd.matrix_client.add_ephemeral_listener(self.global_event)

        vd.matrix_client.start_listener_thread(exception_handler=vd.exceptionCaught)

        vd.matrix_client._sync()

        vd.matrix_client.listen_for_events() # vd.matrix_client.sync(full_state=True)

    @asyncthread
    def add_room(self, room):
        room.add_listener(self.room_event)
        room.add_ephemeral_listener(self.room_event)
        room.add_state_listener(self.global_event)
        room.backfill_previous_messages(limit=1)

    def addRow(self, r, **kwargs):
        r = AttrDict(r)
        if r.event_id not in self.event_index:
            super().addRow(r, **kwargs)
            self.event_index[r.event_id] = r

    def global_event(self, chunk):
        self.addRow(chunk)

    def room_event(self, room, chunk):
        ev = AttrDict(chunk)
        t = chunk['type']
        if t == 'm.receipt':
            for msgid, content in chunk['content'].items():
                msg = self.event_index.setdefault(msgid, {})
                if 'received' not in msg:
                    msg['received'] = {}

                for t, c in content.items():
                    assert t == 'm.read'
                    for userid, v in c.items():
                        msg['received'][(t, userid)] = v['ts']/1000
            return

        chunk['room'] = room
        self.addRow(chunk)

    def add_message(self, text):
        vd.matrix_client.send_text(text)


MatrixSheet.init('event_index', dict)

MatrixSheet.addCommand('a', 'add-message', 'cursorRow.room.send_text(input(cursorRow.room.display_name+"> "))')
MatrixSheet.addCommand('', 'dive-row', 'vd.push(MatrixRoom(cursorRow.room.display_name, source=cursorRow.room))')
