from contextlib import suppress
import collections
import curses

import visidata

from visidata import EscapeException, ExpectedException, clipdraw, Sheet, VisiData
from visidata import vd, options, colors
from visidata import suspend, ColumnItem, AttrDict


vd.option('color_edit_cell', 'white', 'cell color to use when editing cell')
vd.option('disp_edit_fill', '_', 'edit field fill character')
vd.option('disp_unprintable', '·', 'substitute character for unprintables')

vd.option('input_history', '', 'basename of file to store persistent input history')

class AcceptInput(Exception):
    '*args[0]* is the input to be accepted'

visidata.vd._nextCommands = []

@VisiData.api
def queueCommand(vd, longname): #, input=None, sheet=None, col=None, row=None):
    vd._nextCommands.append(longname)

def acceptThenFunc(*longnames):
    def _acceptthen(v, i):
        for longname in longnames:
            vd.queueCommand(longname)
        raise AcceptInput(v)
    return _acceptthen

# editline helpers

class EnableCursor:
    def __enter__(self):
        with suppress(curses.error):
            curses.mousemask(0)
            curses.curs_set(1)

    def __exit__(self, exc_type, exc_val, tb):
        with suppress(curses.error):
            curses.curs_set(0)
            if options.mouse_interval:
                curses.mousemask(curses.MOUSE_ALL if hasattr(curses, "MOUSE_ALL") else 0xffffffff)
            else:
                curses.mousemask(0)


def until_get_wch(scr):
    'Ignores get_wch timeouts'
    ret = None
    while not ret:
        try:
            ret = scr.get_wch()
        except curses.error:
            pass

    return ret


def splice(v, i, s):
    'Insert `s` into string `v` at `i` (such that v[i] == s[0]).'
    return v if i < 0 else v[:i] + s + v[i:]


def clean_printable(s):
    'Escape unprintable characters.'
    return ''.join(c if c.isprintable() else options.disp_unprintable for c in str(s))


def delchar(s, i, remove=1):
    'Delete `remove` characters from str `s` beginning at position `i`.'
    return s if i < 0 else s[:i] + s[i+remove:]


class CompleteState:
    def __init__(self, completer_func):
        self.comps_idx = -1
        self.completer_func = completer_func
        self.former_i = None
        self.just_completed = False

    def complete(self, v, i, state_incr):
        self.just_completed = True
        self.comps_idx += state_incr

        if self.former_i is None:
            self.former_i = i
        try:
            r = self.completer_func(v[:self.former_i], self.comps_idx)
        except Exception as e:
            # raise  # beep/flash; how to report exception?
            return v, i

        if not r:
            # beep/flash to indicate no matches?
            return v, i

        v = r + v[i:]
        return v, len(v)

    def reset(self):
        if self.just_completed:
            self.just_completed = False
        else:
            self.former_i = None
            self.comps_idx = -1

class HistoryState:
    def __init__(self, history):
        self.history = history
        self.hist_idx = None
        self.prev_val = None

    def up(self, v, i):
        if self.hist_idx is None:
            self.hist_idx = len(self.history)
            self.prev_val = v
        if self.hist_idx > 0:
            self.hist_idx -= 1
            v = self.history[self.hist_idx]
        i = len(str(v))
        return v, i

    def down(self, v, i):
        if self.hist_idx is None:
            return v, i
        elif self.hist_idx < len(self.history)-1:
            self.hist_idx += 1
            v = self.history[self.hist_idx]
        else:
            v = self.prev_val
            self.hist_idx = None
        i = len(str(v))
        return v, i


# history: earliest entry first
@VisiData.api
def editline(vd, scr, y, x, w, i=0, attr=curses.A_NORMAL, value='', fillchar=' ', truncchar='-', unprintablechar='.', completer=lambda text,idx: None, history=[], display=True, updater=lambda val: None, bindings={}, clear=True):
  '''A better curses line editing widget.
  If *clear* is True, clear whole editing area before displaying.
  '''
  with EnableCursor():
    ESC='^['
    TAB='^I'

    history_state = HistoryState(history)
    complete_state = CompleteState(completer)
    insert_mode = True
    first_action = True
    v = str(value)  # value under edit

    # i = 0  # index into v, initial value can be passed in as argument as of 1.2
    if i != 0:
        first_action = False

    left_truncchar = right_truncchar = truncchar

    def find_nonword(s, a, b, incr):
        if not s: return 0
        a = min(max(a, 0), len(s)-1)
        b = min(max(b, 0), len(s)-1)

        if incr < 0:
            while not s[b].isalnum() and b >= a:  # first skip non-word chars
                b += incr
            while s[b].isalnum() and b >= a:
                b += incr
            return min(max(b, -1), len(s))
        else:
            while not s[a].isalnum() and a < b:  # first skip non-word chars
                a += incr
            while s[a].isalnum() and a < b:
                a += incr
            return min(max(a, 0), len(s))


    while True:
        updater(v)
        vd.getHelpPane('input', module=__name__).draw(scr, y=y)

        if display:
            dispval = clean_printable(v)
        else:
            dispval = '*' * len(v)

        dispi = i  # the onscreen offset within the field where v[i] is displayed
        if len(dispval) < w:  # entire value fits
            dispval += fillchar*(w-len(dispval)-1)
        elif i == len(dispval):  # cursor after value (will append)
            dispi = w-1
            dispval = left_truncchar + dispval[len(dispval)-w+2:] + fillchar
        elif i >= len(dispval)-w//2:  # cursor within halfwidth of end
            dispi = w-(len(dispval)-i)
            dispval = left_truncchar + dispval[len(dispval)-w+1:]
        elif i <= w//2:  # cursor within halfwidth of beginning
            dispval = dispval[:w-1] + right_truncchar
        else:
            dispi = w//2  # visual cursor stays right in the middle
            k = 1 if w%2==0 else 0  # odd widths have one character more
            dispval = left_truncchar + dispval[i-w//2+1:i+w//2-k] + right_truncchar

        prew = clipdraw(scr, y, x, dispval[:dispi], attr, w, clear=clear)
        clipdraw(scr, y, x+prew, dispval[dispi:], attr, w-prew+1, clear=clear)
        scr.move(y, x+prew)
        ch = vd.getkeystroke(scr)
        if ch == '':                               continue
        elif ch == 'KEY_IC':                       insert_mode = not insert_mode
        elif ch == '^A' or ch == 'KEY_HOME':       i = 0
        elif ch == '^B' or ch == 'KEY_LEFT':       i -= 1
        elif ch in ('^C', '^Q', ESC):              raise EscapeException(ch)
        elif ch == '^D' or ch == 'KEY_DC':         v = delchar(v, i)
        elif ch == '^E' or ch == 'KEY_END':        i = len(v)
        elif ch == '^F' or ch == 'KEY_RIGHT':      i += 1
        elif ch == '^G':                           vd.show_help = not vd.show_help; continue # not a first keypress
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1; v = delchar(v, i)
        elif ch == TAB:                            v, i = complete_state.complete(v, i, +1)
        elif ch == 'KEY_BTAB':                     v, i = complete_state.complete(v, i, -1)
        elif ch in ['^J', '^M']:                   break  # ENTER to accept value
        elif ch == '^K':                           v = v[:i]  # ^Kill to end-of-line
        elif ch == '^O':                           v = vd.launchExternalEditor(v)
        elif ch == '^R':                           v = str(value)  # ^Reload initial value
        elif ch == '^T':                           v = delchar(splice(v, i-2, v[i-1]), i)  # swap chars
        elif ch == '^U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == '^V':                           v = splice(v, i, until_get_wch(scr)); i += 1  # literal character
        elif ch == '^W':                           j = find_nonword(v, 0, i-1, -1); v = v[:j+1] + v[i:]; i = j+1  # erase word
        elif ch == '^Y':                           v = splice(v, i, vd.memory.clipval)
        elif ch == '^Z':                           suspend()
        # CTRL+arrow
        elif ch == 'kLFT5':                        i = find_nonword(v, 0, i-1, -1)+1; # word left
        elif ch == 'kRIT5':                        i = find_nonword(v, i+1, len(v)-1, +1)+1; # word right
        elif ch == 'kUP5':                         pass
        elif ch == 'kDN5':                         pass
        elif history and ch == 'KEY_UP':           v, i = history_state.up(v, i)
        elif history and ch == 'KEY_DOWN':         v, i = history_state.down(v, i)
        elif ch in bindings:                       v, i = bindings[ch](v, i)
        elif len(ch) > 1:                          pass
        else:
            if first_action:
                v = ''
            if insert_mode:
                v = splice(v, i, ch)
            else:
                v = v[:i] + ch + v[i+1:]

            i += 1

        if i < 0: i = 0
        # v may have a non-str type with no len()
        v = str(v)
        if i > len(v): i = len(v)
        first_action = False
        complete_state.reset()

    return type(value)(v)


@VisiData.api
def editText(vd, y, x, w, record=True, display=True, **kwargs):
    'Invoke modal single-line editor at (*y*, *x*) for *w* terminal chars. Use *display* is False for sensitive input like passphrases.  If *record* is True, get input from the cmdlog in batch mode, and save input to the cmdlog if *display* is also True. Return new value as string.'
    v = None
    if record and vd.cmdlog:
        v = vd.getLastArgs()

    if v is None:
        try:
            v = vd.editline(vd.activeSheet._scr, y, x, w, display=display, **kwargs)
        except AcceptInput as e:
            v = e.args[0]

        if vd.scrFull:  # check if curses initialised
            # clear keyboard buffer to neutralize multi-line pastes (issue#585)
            curses.flushinp()

    if display:
        vd.status('"%s"' % v)
        if record and vd.cmdlog:
            vd.setLastArgs(v)

    return v


@VisiData.api
def inputsingle(vd, prompt, record=True):
    'Display prompt and return single character of user input.'
    sheet = vd.activeSheet
    rstatuslen = vd.drawRightStatus(sheet._scr, sheet)

    v = None
    if record and vd.cmdlog:
        v = vd.getLastArgs()

    if v is not None:
        return v

    y = sheet.windowHeight-1
    w = sheet.windowWidth
    rstatuslen = vd.drawRightStatus(sheet._scr, sheet)
    promptlen = clipdraw(sheet._scr, y, 0, prompt, 0, w=w-rstatuslen-1)
    sheet._scr.move(y, w-promptlen-rstatuslen-2)
    v = vd.getkeystroke(sheet._scr)

    if record and vd.cmdlog:
        vd.setLastArgs(v)

    return v


@VisiData.api
def input(self, prompt, type=None, defaultLast=False, history=[], **kwargs):
    '''Display *prompt* and return line of user input.

        - *type*: string indicating the type of input to use for history.
        - *history*: list of strings to use for input history.
        - *defaultLast*:  on empty input, if True, return last history item.
        - *display*: pass False to not display input (for sensitive input, e.g. a password).
        - *record*: pass False to not record input on cmdlog (for sensitive or inconsequential input).
        - *completer*: ``completer(val, idx)`` is called on TAB to get next completed value.
        - *updater*: ``updater(val)`` is called every keypress or timeout.
        - *bindings*: dict of keystroke to func(v, i) that returns updated (v, i)
    '''

    history = self.lastInputsSheet.history(type)

    sheet = self.activeSheet
    rstatuslen = self.drawRightStatus(sheet._scr, sheet)
    attr = 0
    promptlen = clipdraw(sheet._scr, sheet.windowHeight-1, 0, prompt, attr, w=sheet.windowWidth-rstatuslen-1)
    ret = self.editText(sheet.windowHeight-1, promptlen, sheet.windowWidth-promptlen-rstatuslen-2,
                        attr=colors.color_edit_cell,
                        unprintablechar=options.disp_unprintable,
                        truncchar=options.disp_truncator,
                        history=history,
                        **kwargs)

    if ret:
        self.lastInputsSheet.appendRow(AttrDict(type=type, input=ret))

    elif defaultLast:
        history or vd.fail("no previous input")
        ret = history[-1]

    return ret


@VisiData.api
def confirm(vd, prompt, exc=EscapeException):
    'Display *prompt* on status line and demand input that starts with "Y" or "y" to proceed.  Raise *exc* otherwise.  Return True.'
    if options.batch:
        return vd.fail('cannot confirm in batch mode: ' + prompt)

    yn = vd.input(prompt, value='no', record=False)[:1]
    if not yn or yn not in 'Yy':
        msg = 'disconfirmed: ' + prompt
        if exc:
            raise exc(msg)
        vd.warning(msg)
        return False
    return True


class CompleteKey:
    def __init__(self, items):
        self.items = items

    def __call__(self, val, state):
        opts = [x for x in self.items if x.startswith(val)]
        return opts[state%len(opts)] if opts else val


@Sheet.api
def editCell(self, vcolidx=None, rowidx=None, value=None, **kwargs):
    '''Call vd.editText for the cell at (*rowidx*, *vcolidx*).  Return the new value, properly typed.

       - *rowidx*: numeric index into ``self.rows``.  If negative, indicates the column name in the header.
       - *value*: if given, the starting input; otherwise the starting input is the cell value or column name as appropriate.
       - *kwargs*: passthrough args to ``vd.editText``.
       '''

    if vcolidx is None:
        vcolidx = self.cursorVisibleColIndex
    x, w = self._visibleColLayout.get(vcolidx, (0, 0))

    col = self.visibleCols[vcolidx]
    if rowidx is None:
        rowidx = self.cursorRowIndex

    if rowidx < 0:  # header
        y = 0
        value = value or col.name
    else:
        y, h = self._rowLayout.get(rowidx, (0, 0))
        value = value or col.getDisplayValue(self.rows[self.cursorRowIndex])

    bindings={
        'kUP':        acceptThenFunc('go-up', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'KEY_SR':     acceptThenFunc('go-up', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'kDN':        acceptThenFunc('go-down', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'KEY_SF':     acceptThenFunc('go-down', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'KEY_SRIGHT': acceptThenFunc('go-right', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'KEY_SLEFT':  acceptThenFunc('go-left', 'rename-col' if rowidx < 0 else 'edit-cell'),
    }

    bindings.update(kwargs.get('bindings', {}))
    kwargs['bindings'] = bindings

    editargs = dict(value=value,
                    fillchar=options.disp_edit_fill,
                    truncchar=options.disp_truncator)

    editargs.update(kwargs)  # update with user-specified args
    r = vd.editText(y, x, w, **editargs)

    if rowidx >= 0:  # if not header
        r = col.type(r)  # convert input to column type, let exceptions be raised

    return r


vd.addGlobals({'CompleteKey': CompleteKey})
