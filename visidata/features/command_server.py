# ailevel 6

import io
import json
import os
import socket
import stat
import time

from visidata import vd, VisiData, asyncignore, Sheet
from visidata.statusbar import composeStatus


vd.option('server_addr', '127.0.0.1', 'IP address to listen for commands', sheettype=None, replay=False)
vd.option('server_port', 0, 'port to listen for commands', sheettype=None, replay=False)
vd.option('server_socket', '', 'path to Unix domain socket to listen for commands (takes precedence over server_port)', sheettype=None, replay=False)
vd.option('server_cursor_width', 200, 'max display width per cell in cursor row echo', sheettype=None, replay=False)


class ScreenBuffer:
    'Fake curses screen that captures addstr calls into a character grid.'
    def __init__(self, h=25, w=80):
        self.h = h
        self.w = w
        self.buf = [[' '] * w for _ in range(h)]

    def getmaxyx(self):
        return (self.h, self.w)

    def addstr(self, y, x, s, attr=0):
        if y < 0 or y >= self.h:
            return
        for i, ch in enumerate(s):
            if x + i >= self.w:
                break
            if x + i >= 0:
                self.buf[y][x + i] = ch

    def erase(self):
        self.buf = [[' '] * self.w for _ in range(self.h)]

    def bkgd(self, ch=' ', attr=0):
        pass

    def move(self, y, x):
        pass

    def refresh(self):
        pass

    def to_text(self):
        'Return buffer contents as plain text, trailing spaces stripped.'
        return '\n'.join(''.join(row).rstrip() for row in self.buf).rstrip('\n')


def _wait_for_idle(timeout=0.5):
    'Wait up to *timeout* seconds for command queue to drain and sheet threads to finish.'
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not vd._nextCommands and not vd.sheet.currentThreads:
            return True
        time.sleep(0.05)
    return False


def _capture_screen():
    'Render current sheet to a text screen buffer and return as plain text.'
    sheet = vd.sheet
    if not sheet:
        return ''

    scr = ScreenBuffer(h=sheet.windowHeight, w=sheet.windowWidth)
    vd.drawSheet(scr, sheet)

    # add < marker at end of cursor row
    cursor_layout = sheet._rowLayout.get(sheet.cursorRowIndex)
    if cursor_layout:
        cursor_y = cursor_layout[0]
        # find rightmost non-space character on cursor row
        row = scr.buf[cursor_y]
        end = len(row) - 1
        while end >= 0 and row[end] == ' ':
            end -= 1
        mark_x = min(end + 1, scr.w - 1)
        scr.buf[cursor_y][mark_x] = '<'

    text = scr.to_text()

    # append structured context lines for programmatic consumers

    # cursor row echo: full content, capped at server_cursor_width per cell
    currow = sheet.cursorRow if hasattr(sheet, 'cursorRow') else None
    curcol = sheet.cursorCol
    if currow is not None:
        w = sheet.options.server_cursor_width
        parts = []
        for col in sheet.visibleCols:
            try:
                typedval = col.getTypedValue(currow)
                v = col.format(typedval, width=w) or ''
                parts.append(f'{col.name}={v}')
            except Exception:
                parts.append(f'{col.name}=?')
        text += f'\ncursor ({sheet.cursorRowIndex}/{sheet.nRows}): ' + ' | '.join(parts)
    if curcol:
        text += f'\ncursor col: "{curcol.name}"'

    # sheet stack with shortcut numbers (use jump-sheet-N to navigate)
    sheets = vd.sheets
    parts = [f'{s.shortcut}:{s.name}' for s in reversed(sheets)]
    text += '\nsheets: ' + ' > '.join(parts)

    # selection state (so caller notices stale selections)
    nsel = sheet.nSelectedRows
    if nsel:
        text += f'\nselected: {nsel}/{sheet.nRows} rows'

    return text


def _capture_progress():
    'Return machine-consumable progress info for current sheet.'
    sheet = vd.sheet
    threads = sheet.currentThreads if sheet else []
    gerunds = [p.gerund for p in sheet.progresses if p.gerund] if sheet else []
    return dict(
        _type='progress',
        threads=len(threads),
        pct=sheet.progressPct.strip() if sheet else '',
        gerund=gerunds[0] if gerunds else '',
        queued_commands=len(vd._nextCommands),
    )


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
    sock_path = vd.options.server_socket
    port = vd.options.server_port
    if sock_path:
        vd.timeouts_before_idle = -1  # never block indefinitely on getch when server is active
        vd.unix_command_listener(sock_path)
    elif port:
        vd.timeouts_before_idle = -1  # never block indefinitely on getch when server is active
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
        vd.debug(f'Connection from {addr}:{inport}')
        vd.queueCommand('no-op')  # update screen

        vd.command_server(conn)


@VisiData.api
@asyncignore
def unix_command_listener(vd, path):
    # refuse-to-clobber: only unlink if existing path is a socket
    if os.path.lexists(path) and not stat.S_ISSOCK(os.lstat(path).st_mode):
        vd.fail(f'server_socket path {path!r} exists and is not a socket')
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    # bind once and accept many to avoid an unlink/rebind race between connections
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(path)
    s.listen(5)
    while True:
        conn, _ = s.accept()
        vd.debug(f'Connection on {path}')
        vd.queueCommand('no-op')  # update screen

        vd.command_server(conn)


@VisiData.api
@asyncignore
def command_server(vd, conn):
    def _send(obj):
        conn.send(json.dumps(obj).encode('utf-8', errors='replace') + b'\n')

    for line in SocketIO(conn):
        line = line.decode().strip()
        if not line:
            continue
        if line == 'draw':
            r = '\n'.join(json.dumps(d) for d in vd.sheet.capture_draw_object())
            conn.send(r.encode('utf-8', errors='replace')+b'\n')
        elif line == 'get-progress':
            _send(_capture_progress())
        elif line == 'screen':
            text = _capture_screen()
            if vd.statuses:
                for (priority, msgparts), count in vd.statuses.items():
                    text += '\n' + composeStatus(msgparts, count)
                vd.statuses.clear()
            conn.send(text.encode('utf-8', errors='replace') + b'\n')
        elif line == 'cancel-sheet':
            vd._nextCommands.clear()
            sheet = vd.sheet
            if sheet and sheet.currentThreads:
                vd.cancelThread(*sheet.currentThreads)
        elif line == 'cancel-all':
            vd._nextCommands.clear()
            threads = [t for vs in vd.sheets for t in vs.currentThreads]
            if threads:
                vd.cancelThread(*threads)
        elif line == 'sync':
            _wait_for_idle(timeout=60)
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

    yield dict(
        _type='sheet',
        name=sheet.name,
        nRows=sheet.nRows,
        cursorRowIndex=sheet.cursorRowIndex,
        cursorColIndex=sheet.cursorColIndex,
        nSelectedRows=sheet.nSelectedRows,
        topRowIndex=topRowIndex,
    )

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

    for (priority, msgparts), count in vd.statuses.items():
        yield dict(_type='status', priority=priority, message=' '.join(msgparts), count=count)

    yield _capture_progress()
