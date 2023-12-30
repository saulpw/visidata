import io
import json
import socket
from unittest.mock import Mock

from visidata import vd, VisiData, asyncthread, asyncignore, CommandLogRow, Sheet


vd.option('server_addr', '127.0.0.1', 'IP address to listen for commands', sheettype=None, replay=False)
vd.option('server_port', 0, 'port to listen for commands', sheettype=None, replay=False)


class SocketIO(io.RawIOBase):
    def __init__(self, sock):
        self.sock = sock

    def read(self, sz=-1):
        if (sz == -1): sz=0x7FFFFFFF
        return self.sock.recv(sz)

    def seekable(self):
        return False


@VisiData.before
def mainloop(vd, scr):
    port = vd.options.server_port
    if port:
        vd.command_listener(vd.options.server_addr, port)


@VisiData.api
@asyncignore
def command_listener(vd, addr, port):
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((addr, port))
        s.listen(1)

        conn, (addr, inport) = s.accept()
        vd.status(f'Connection from {addr}:{inport}')
        vd.queueCommand('no-op')  # update screen
        vd.command_server(conn)


@VisiData.api
@asyncignore
def command_server(vd, conn):
    for line in SocketIO(conn):
        line = line.decode().strip()
        if line == 'draw':
            r = '\n'.join(json.dumps(d) for d in vd.sheet.capture_draw_object())
            conn.send(r.encode('utf-8')+b'\n')
        elif line.startswith('{'):
            cmd = json.loads(line)
            vd.queueCommand(**cmd)
        else:
            longname, *rest = line.split(' ', maxsplit=1)
            cmd = dict(longname=longname, input=rest[0] if rest else '')
            vd.queueCommand(**cmd)

    conn.close()


@Sheet.api
def capture_draw_object(sheet, topRowIndex=0, nScreenRows=25):
    'capture interface at the object level'
    isNull = sheet.isNullFunc()
    sortkeys = {col:rev for col, rev in sheet._ordering}
    rows = sheet.rows[topRowIndex:min(topRowIndex+nScreenRows+1, sheet.nRows)]

    for vcolidx, col in enumerate(sheet.visibleCols):
        colstate = col.__getstate__()

        if col in sortkeys:
            colstate['sort'] = 'desc' if sortkeys.get(col) else 'asc'

        yield dict(i=vcolidx, _type='column', **colstate)

    for rowidx, row in enumerate(rows):
        rowstate = dict()

        for notefunc in vd.rowNoters:
            ch = notefunc(sheet, row)
            if ch:
                rowstate['note'] = rowstate.get('note', '') + ch

        for vcolidx, col in enumerate(sheet.visibleCols):
            cellval = col.getCell(row)

            disp = ''.join(x for _, x in col.display(cellval))
            cellstate = dict(display=disp)
            notes = getattr(cellval, 'notes', '')
            try:
                if isNull and isNull(cellval.value):
                    notes += sheet.options.disp_note_none
            except (TypeError, ValueError):
                pass

            if notes:
                cellstate['notes'] = notes
            rowstate[str(vcolidx)] = cellstate

        yield dict(_type='row', i=rowidx, **rowstate)
