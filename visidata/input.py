import collections
import curses

from visidata import EscapeException, ExpectedException, EnableCursor, clipdraw, Sheet, VisiData
from visidata import vd, status, error, warning, fail, options, theme, colors, commands
from visidata import launchExternalEditor, suspend

__all__ = ['confirm', 'editline', 'choose', 'chooseOne', 'chooseMany', 'input_longname']

theme('color_edit_cell', 'normal', 'cell color to use when editing cell')
theme('disp_edit_fill', '_', 'edit field fill character')
theme('disp_unprintable', '.', 'substitute character for unprintables')

vd.lastInputs = collections.defaultdict(collections.OrderedDict)  # [input_type] -> prevInputs

# editline helpers

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
    return ''.join(c if c.isprintable() else ('<%04X>' % ord(c)) for c in str(s))


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
        i = len(v)
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
        i = len(v)
        return v, i


# history: earliest entry first
def editline(scr, y, x, w, i=0, attr=curses.A_NORMAL, value='', fillchar=' ', truncchar='-', unprintablechar='.', completer=lambda text,idx: None, history=[], display=True, updater=lambda val: None):
    'A better curses line editing widget.'
    ESC='^['
    ENTER='^J'
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

    def rfind_nonword(s, a, b):
        if not s:
            return 0

        while not s[b].isalnum() and b >= a:  # first skip non-word chars
            b -= 1
        while s[b].isalnum() and b >= a:
            b -= 1
        return b

    while True:
        updater(v)

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

        prew = clipdraw(scr, y, x, dispval[:dispi], attr, w)
        clipdraw(scr, y, x+prew, dispval[dispi:], attr, w-prew+1)
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
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1; v = delchar(v, i)
        elif ch == TAB:                            v, i = complete_state.complete(v, i, +1)
        elif ch == 'KEY_BTAB':                     v, i = complete_state.complete(v, i, -1)
        elif ch == ENTER:                          break
        elif ch == '^K':                           v = v[:i]  # ^Kill to end-of-line
        elif ch == '^O':                           v = launchExternalEditor(v)
        elif ch == '^R':                           v = str(value)  # ^Reload initial value
        elif ch == '^T':                           v = delchar(splice(v, i-2, v[i-1]), i)  # swap chars
        elif ch == '^U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == '^V':                           v = splice(v, i, until_get_wch(scr)); i += 1  # literal character
        elif ch == '^W':                           j = rfind_nonword(v, 0, i-1); v = v[:j+1] + v[i:]; i = j+1  # erase word
        elif ch == '^Z':                           suspend()
        elif history and ch == 'KEY_UP':           v, i = history_state.up(v, i)
        elif history and ch == 'KEY_DOWN':         v, i = history_state.down(v, i)
        elif ch.startswith('KEY_'):                pass
        else:
            if first_action:
                v = ''
            if insert_mode:
                v = splice(v, i, ch)
            else:
                v = v[:i] + ch + v[i+1:]

            i += 1

        if i < 0: i = 0
        if i > len(v): i = len(v)
        first_action = False
        complete_state.reset()

    return v


@VisiData.api
def editText(self, y, x, w, record=True, **kwargs):
    'Wrap global editText with `preedit` and `postedit` hooks.'
    v = None
    if record and self.cmdlog:
        v = self.cmdlog.getLastArgs()

    if v is None:
        with EnableCursor():
            v = editline(self.scr, y, x, w, **kwargs)

    if kwargs.get('display', True):
        status('"%s"' % v)
        if record and self.cmdlog:
            self.cmdlog.setLastArgs(v)
    return v


@VisiData.api
def input(self, prompt, type='', defaultLast=False, **kwargs):
    'Get user input, with history of `type`, defaulting to last history item if no input and defaultLast is True.'
    if type:
        histlist = list(self.lastInputs[type].keys())
        ret = self._inputLine(prompt, history=histlist, **kwargs)
        if ret:
            self.lastInputs[type][ret] = ret
        elif defaultLast:
            histlist or fail("no previous input")
            ret = histlist[-1]
    else:
        ret = self._inputLine(prompt, **kwargs)

    return ret


@VisiData.api
def _inputLine(self, prompt, **kwargs):
    'Add prompt to bottom of screen and get line of input from user.'
    rstatuslen = self.drawRightStatus(self.scr, self.sheets[0])
    attr = 0
    promptlen = clipdraw(self.scr, self.windowHeight-1, 0, prompt, attr, w=self.windowWidth-rstatuslen-1)
    ret = self.editText(self.windowHeight-1, promptlen, self.windowWidth-promptlen-rstatuslen-2,
                        attr=colors.color_edit_cell,
                        unprintablechar=options.disp_unprintable,
                        truncchar=options.disp_truncator,
                        **kwargs)
    return ret


def confirm(prompt, exc=ExpectedException):
    yn = vd.input(prompt, value='no', record=False)[:1]
    if not yn or yn not in 'Yy':
        if exc:
            raise exc('disconfirmed')
        warning('disconfirmed')
        return False
    return True


class CompleteKey:
    def __init__(self, items):
        self.items = items

    def __call__(self, val, state):
        opts = [x for x in self.items if x.startswith(val)]
        return opts[state%len(opts)] if opts else val


def input_longname(sheet):
    longnames = set(k for (k, obj), v in commands.iter(sheet))
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)))


def chooseOne(L):
    return choose(L, 1)


def choose(choices, n=None):
    'Return one of `choices` elements (if list) or values (if dict).'
    ret = chooseMany(choices) or fail('no choice made')
    if n and len(ret) > n:
        error('can only choose %s' % n)
    return ret[0] if n==1 else ret


def chooseMany(choices):
    'Return list of `choices` elements (if list) or values (if dict).'
    if isinstance(choices, dict):
        prompt = '/'.join(choices.keys())
        chosen = []
        for c in vd.input(prompt+': ', completer=CompleteKey(choices)).split():
            poss = [choices[p] for p in choices if p.startswith(c)]
            if not poss:
                warning('invalid choice "%s"' % c)
            else:
                chosen.extend(poss)
    else:
        prompt = '/'.join(str(x) for x in choices)
        chosen = []
        for c in vd.input(prompt+': ', completer=CompleteKey(choices)).split():
            poss = [p for p in choices if p.startswith(c)]
            if not poss:
                warning('invalid choice "%s"' % c)
            else:
                chosen.extend(poss)
    return chosen


@Sheet.api
def edit(self, col, row, **kwargs):
    'Call `editText` at its place on the screen.  Returns the new value, properly typed'

    vcolidx = self.visibleCols.index(col)
    x, w = self.visibleColLayout.get(vcolidx, (0, 0))

    if row is None:  # header
        rowidx = -1
        y = 0
        currentValue = col.name
    else:
        for rowidx, y in self.rowLayout.items():
            if self.rows[rowidx] is row:
                break  # let y be as it is
        currentValue = col.getDisplayValue(row)

    editargs = dict(value=currentValue,
                    fillchar=options.disp_edit_fill,
                    truncchar=options.disp_truncator)
    editargs.update(kwargs)  # update with user-specified args
    r = vd.editText(y, x, w, **editargs)
    if row is not None:  # if not header
        r = col.type(r)  # convert input to column type, let exceptions be raised

    return r
