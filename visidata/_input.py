from contextlib import suppress
import curses
import json

import visidata

from visidata import EscapeException, ExpectedException, clipdraw, Sheet, VisiData, BaseSheet
from visidata import vd, colors, dispwidth, ColorAttr, clipstr_start
from visidata import AttrDict


vd.option('confirm', 'a', 'confirm interactive prompts {a=ask|y=yes}')

vd.theme_option('color_edit_unfocused', '238 on 110', 'display color for unfocused input in form')
vd.theme_option('color_edit_cell', '233 on 110', 'cell color to use when editing cell')
vd.theme_option('disp_edit_fill', '_', 'edit field fill character')
vd.theme_option('disp_unprintable', '·', 'substitute character for unprintables')
vd.theme_option('mouse_interval', 1, 'max time between press/release for click (ms)', sheettype=None)


class AcceptInput(Exception):
    '*args[0]* is the input to be accepted'

vd._injectedInput = None  # for vd.injectInput
vd.editCellBindings = {}  # user-customizable bindings for cell editing; use acceptThenFunc() to define


@VisiData.api
def injectInput(vd, x):
    'Use *x* as input to next command.'
    assert vd._injectedInput is None, vd._injectedInput
    vd._injectedInput = x


@VisiData.api
def getCommandInput(vd):
    if vd._injectedInput is not None:
        r = vd._injectedInput
        vd._injectedInput = None
        return r

    return vd.getLastArgs()


@BaseSheet.after
def execCommand(sheet, longname, *args, **kwargs):
    if vd._injectedInput is not None:
        vd.debug(f'{longname} did not consume input "{vd._injectedInput}"')
        vd._injectedInput = None


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
            vd.enableMouse(False)
            curses.curs_set(1)

    def __exit__(self, exc_type, exc_val, tb):
        with suppress(curses.error):
            curses.curs_set(0)
            vd.enableMouse(bool(vd.options.mouse_interval))


def until_get_wch(scr):
    'Ignores get_wch timeouts'
    ret = None
    while not ret:
        try:
            ret = vd.get_wch(scr)
        except curses.error:
            pass

    if isinstance(ret, int):
        return chr(ret)
    return ret


def splice(v:str, i:int, s:str):
    'Insert `s` into string `v` at `i` (such that v[i] == s[0]).'
    return v if i < 0 else v[:i] + s + v[i:]


@VisiData.api
def drawInputHelp(vd, scr):
    if not scr or not vd.cursesEnabled:
        return

    sheet = vd.activeSheet
    if not sheet:
        return

    vd.drawSidebar(scr, sheet)


def clean_printable(s):
    'Escape unprintable characters.'
    return ''.join(c if c.isprintable() else vd.options.disp_unprintable for c in str(s))


def delchar(s, i, remove=1):
    'Delete `remove` characters from str `s` beginning at position `i`.'
    return s if i < 0 else s[:i] + s[i+remove:]

def find_word(s, a, b, incr):
        '''Return first index of word boundary in s[a:b], going forward if incr is +1 and backward if incr is -1.'''
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
            while s[a].isalnum() and a < b:       # first skip word chars
                a += incr
            while not s[a].isalnum() and a < b:   # then skip non-word chars
                a += incr
            return min(max(a, 0), len(s))

class InputWidget:
    def __init__(self,
                 value:str='',
                 i=0,
                 display=True,
                 history=[],
                 completer=lambda text,idx: None,
                 options=None,
                 fillchar=''):
        '''
            - value: starting value
            - i: starting index into value
            - display: False to not display input (for sensitive input, e.g. a password)
            - history: list of strings; earliest entry first.
            - completer: func(value:str, idx:int) takes the current value and tab completion index, and returns a string if there is a completion available, or None if not.
            - options: sheet.options; defaults to vd.options.
        '''
        options = options or vd.options

        self.orig_value = value
        self.first_action = (i == 0)  # whether this would be the 'first action'; if so, clear text on input

        # display theme
        self.fillchar  = fillchar or options.disp_edit_fill
        self.truncchar = options.disp_truncator
        self.display = display  # if False, obscure before displaying

        # main state
        self.value = self.orig_value  # value under edit
        self.current_i = i
        self.insert_mode = True

        # history state
        self.history = history
        self.hist_idx = None
        self.prev_val = None

        # completion state
        self.comps_idx = -1
        self.completer_func = completer
        self.former_i = None
        self.just_completed = False

    def editline(self, scr, y, x, w, attr=ColorAttr(), updater=lambda val:None, bindings={}, clear=True) -> str:
        'If *clear* is True, clear whole editing area before displaying.'
        with EnableCursor():
            while True:
                if len(vd.pendingKeys) <= 3:  #speed up paste of long strings by skipping redraws
                    vd.drawSheet(scr, vd.activeSheet)
                    updater(self.value)
                    vd.drawInputHelp(scr)

                self.draw(scr, y, x, w, attr, clear=clear)
                ch = vd.getkeystroke(scr)
                if ch in bindings:
                    self.value, self.current_i = bindings[ch](self.value, self.current_i)
                    self.first_action = False
                else:
                    if self.handle_key(ch, scr):
                        return self.value


    def draw(self, scr, y, x, w, attr=ColorAttr(), clear=True):
        i = self.current_i  # the onscreen offset within the field where v[i] is displayed
        trunch = self.truncchar
        tr_w = dispwidth(trunch)
        fill_w = dispwidth(self.fillchar)

        def _calc_display(dispval, i):
            '''Return a formatted substring of *dispval* that fills the on-screen width *w*.'''
            if i == len(dispval): # add a fillchar so the user perceives room to type
                dispval += self.fillchar
            dw = dispwidth(dispval, literal=True)
            if dw <= w:  # entire value fits
                dispval += self.fillchar*(w-dw)
                return dispval, i
            if w <= tr_w: # column is too narrow to hold a left and right truncation
                return trunch, 0

            dw = dispwidth(dispval[i:], literal=True)
            if dw + tr_w <= w and dw <= w//2: #cursor is within half-colwidth of end
                #truncate the left and show the end
                frag, n = clipstr_start(dispval, w-tr_w, literal=True)
                offset = len(dispval) - i
                dispval = ' '*(w-tr_w - n) + trunch + frag
                i = len(dispval) - offset
                return dispval, i

            # the remaining cases need the right side truncated, after the new dispval is returned
            dw = dispwidth(dispval[:i+1], literal=True)
            if dw + tr_w <= w and dispwidth(dispval[:i], literal=True) <= w//2: #cursor is within half-colwidth of start
                #truncate the right, and show the string start
                pass
            else: # truncate left and right sides
                # Place the cursor at the midpoint of the available colwidth
                left_w = (w - 2*tr_w)//2
                # calculate the fragment to the left of the cursor
                l_frag, n = clipstr_start(dispval[:i], left_w, literal=True)
                dispval = ' '*(left_w-n) + trunch + l_frag + dispval[i:]
                i = left_w-n + len(trunch) + len(l_frag)
            return dispval, i

        if self.display:
            dispval = clean_printable(self.value)
        else:
            dispval = '*' * len(self.value)
        dispval, i = _calc_display(dispval, i)

        #clipdraw will truncate the right side of dispval with trunch as needed
        clipdraw(scr, y, x, dispval, attr, w, clear=clear, literal=True)
        if x+w < scr.getmaxyx()[1]:
            #draw a space to indicate that the user can scroll right of the cell's final char
            clipdraw(scr, y, x+w, ' ', attr, 1, clear=False, literal=True)
        if scr:
            prew = dispwidth(dispval[:i], literal=True)
            if x+prew < scr.getmaxyx()[1]: #move cursor back to where the user is editing
                scr.move(y, x+prew)

    def handle_key(self, ch:str, scr) -> bool:
        'Return True to accept current input.  Raise EscapeException on Ctrl+C, Ctrl+Q, or ESC.'
        i = self.current_i
        v = self.value

        if ch == '':                               return False
        elif ch == 'Ins':                          self.insert_mode = not self.insert_mode
        elif ch == 'Ctrl+A' or ch == 'Home':       i = 0
        elif ch == 'Ctrl+B' or ch == 'Left':       i -= 1
        elif ch in ('Ctrl+C', 'Ctrl+Q', 'Esc'): raise EscapeException(ch)
        elif ch == 'Ctrl+D' or ch == 'Del':        v = delchar(v, i)
        elif ch == 'Ctrl+E' or ch == 'End':        i = len(v)
        elif ch == 'Ctrl+F' or ch == 'Right':      i += 1
        elif ch == 'Ctrl+G':
            vd.cycleSidebar()
            return False # not considered a first keypress
        elif ch in ('Ctrl+H', 'Bksp', 'Ctrl+?'):   i -= 1; v = delchar(v, i)
        elif ch == 'Tab':                          v, i = self.completion(v, i, +1)
        elif ch == 'Shift+Tab':                    v, i = self.completion(v, i, -1)
        elif ch == 'Enter':                        return True # ENTER to accept value
        elif ch == 'Ctrl+K':                       v = v[:i]  # Ctrl+Kill to end-of-line
        elif ch == 'Ctrl+N':
            c = ''
            while not c:
                c = vd.getkeystroke(scr)
            i += len(c)
            v += c
        elif ch == 'Ctrl+O':
            edit_v = vd.launchExternalEditor(v)
            if self.value == edit_v:
                # leave cell unmodified when the editor exits with no change
                raise EscapeException(ch)
            else:
                self.value = edit_v
                return True
        elif ch == 'Ctrl+R':                           v = self.orig_value  # Ctrl+Reload initial value
        elif ch == 'Ctrl+T':                           v = delchar(splice(v, i-2, v[i-1:i]), i)  # swap chars
        elif ch == 'Ctrl+U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == 'Ctrl+V':                           v = splice(v, i, until_get_wch(scr)); i += 1  # literal character
        elif ch in ('Ctrl+W','Alt+Bksp','Ctrl+Bksp'):  j = find_word(v, 0, i-1, -1); v = v[:j+1] + v[i:]; i = j+1  # erase word
        elif ch in ('Ctrl+Del','Alt+Del','Alt+d'):     j = find_word(v, i, len(v)-1, +1); v = v[:i] + v[j:]  # erase word forward
        elif ch == 'Ctrl+Y':                           v = splice(v, i, str(vd.memory.clipval))
        elif ch == 'Ctrl+Z':                           vd.suspend()
        elif ch == 'Ctrl+Left':                        i = find_word(v, 0, i-1, -1)+1;  # word left
        elif ch == 'Ctrl+Right':                       i = find_word(v, i, len(v)-1, +1);  # word right
        elif ch == 'Ctrl+Up':                          pass
        elif ch == 'Ctrl+Down':                        pass
        elif ch == 'Up':
            if self.history: v, i = self.prev_history(v, i)
        elif ch == 'Down':
            if self.history: v, i = self.next_history(v, i)
        elif ch == 'KEY_RESIZE':                       pass
        elif len(ch) > 1:                              vd.warning(f'unknown key {ch}')
        else:
            if self.first_action:
                v = ''
            if self.insert_mode:
                v = splice(v, i, ch)
            else:
                v = v[:i] + ch + v[i+1:]

            i += 1

        if i < 0: i = 0
        # v may have a non-str type with no len()
        v = str(v)
        if i > len(v): i = len(v)
        self.current_i = i
        self.value = v
        self.first_action = False
        self.reset_completion()
        return False

    def completion(self, v, i, state_incr):
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

    def reset_completion(self):
        if self.just_completed:
            self.just_completed = False
        else:
            self.former_i = None
            self.comps_idx = -1

    def prev_history(self, v, i):
        if self.hist_idx is None:
            self.hist_idx = len(self.history)
            self.prev_val = v
        if self.hist_idx > 0:
            self.hist_idx -= 1
            v = self.history[self.hist_idx]
        i = len(str(v))
        return v, i

    def next_history(self, v, i):
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


@VisiData.api
def editText(vd, y, x, w, attr=ColorAttr(), value='',
             help='',
             updater=lambda val: None, bindings={},
             display=True, record=True, clear=True, **kwargs):
    '''Invoke modal single-line editor at (*y*, *x*) for *w* terminal chars. Use *display* is False for sensitive input like passphrases.  If *record* is True, get input from the cmdlog in batch mode, and save input to the cmdlog if *display* is also True. Return new value as string. Callers should handle curses.error, which will be raised if the terminal is resized during the edit, in a way that moves the editor coordinates offscreen.'''
    v = None
    if record and vd.cmdlog:
        v = vd.getCommandInput()

    if v is None:
        if vd.options.batch:
            return ''

        if vd.activeSheet._scr is None:
            raise Exception('active sheet does not have a screen')

        if value is None:
            value = ''

        try:
            widget = InputWidget(value=str(value), display=display, **kwargs)

            with vd.AddedHelp(vd.getHelpPane('input', module='visidata'), 'Input Keystrokes Help', 'inputkeys'), \
                 vd.AddedHelp(help, 'Input Field Help', 'inputfield'):
                v = widget.editline(vd.activeSheet._scr, y, x, w, attr=attr, updater=updater, bindings=bindings, clear=clear)
        except AcceptInput as e:
            v = e.args[0]

        if vd.cursesEnabled:
            # clear keyboard buffer to neutralize multi-line pastes (issue#585)
            curses.flushinp()

    if display:
        if record and vd.cmdlog:
            vd.setLastArgs(v)

    if value:
        t = type(value)
        if isinstance(value, (int, float)) and v[-1] == '%':  #2082
            pct = float(v[:-1])
            v = pct*value/100
            # convert back to type of original value
            v = t(v)
        elif isinstance(v, str) and isinstance(value, (list, tuple, dict)):
            import ast
            v = ast.literal_eval(v)
            if not isinstance(v, t):
                vd.fail(f'error parsing string `{v}` into {t}')
        else:
            v = t(v)

    return v

@VisiData.api
def inputsingle(vd, prompt, record=True):
    'Display prompt and return single character of user input.'
    sheet = vd.activeSheet

    v = None
    if record and vd.cmdlog:
        v = vd.getCommandInput()

    if v is not None:
        return v

    y = sheet.windowHeight-1
    w = sheet.windowWidth
    rstatuslen = vd.drawRightStatus(sheet._scr, sheet)
    promptlen = clipdraw(sheet._scr, y, 0, prompt, 0, w=w-rstatuslen-1, literal=True)
    sheet._scr.move(y, w-promptlen-rstatuslen-2)

    while not v:
        v = vd.getkeystroke(sheet._scr)

    if record and vd.cmdlog:
        vd.setLastArgs(v)

    return v

@VisiData.api
def inputMultiple(vd, updater=lambda val: None, record=True, **kwargs):
    'A simple form, where each input is an entry in `kwargs`, with the key being the key in the returned dict, and the value being a dictionary of kwargs to the singular input().'
    previnput = vd.getCommandInput()
    if previnput is not None:
        ret = None
        if isinstance(previnput, str):
            if previnput.startswith('{'):
                ret = json.loads(previnput)
            else:
                ret = {k:v.get('value', '') for k,v in kwargs.items()}
                primekey = list(ret.keys())[0]
                ret[primekey] = previnput

        if isinstance(previnput, dict):
            ret = previnput

        if ret:
            if record and vd.cmdlog:
                vd.setLastArgs(ret)
            return ret

        assert False, type(previnput)

    sheet = vd.activeSheet  # after replay shortcut: no active sheet during bulk replay-reset
    scr = sheet._scr

    maxw = sheet.windowWidth//2
    attr = colors.color_edit_unfocused

    keys = list(kwargs.keys())
    cur_input_key = keys[0]

    if scr:
        scr.erase()

    for i, (k, v) in enumerate(kwargs.items()):
        v['dy'] = i
        v['w'] = maxw-dispwidth(v.get('prompt'))

    class ChangeInput(Exception):
        pass

    def change_input(offset):
        def _throw(v, i):
            if scr:
                scr.erase()
            raise ChangeInput(v, offset)
        return _throw

    def _drawPrompt(val):
        for k, v in kwargs.items():
            #recalculate y to adjust for screen resizes during input()
            y = sheet.windowHeight-v.get('dy')-1
            maxw = min(sheet.windowWidth-1, max(dispwidth(v.get('prompt'), literal=True),
                                                dispwidth(str(v.get('value', '')), literal=True)))
            promptlen = clipdraw(scr, y, 0, v.get('prompt'), attr, w=maxw, literal=True)  #1947
            promptlen = clipdraw(scr, y, promptlen, v.get('value', ''),  attr, w=maxw, literal=True)

        return updater(val)

    while True:
        try:
            input_kwargs = kwargs[cur_input_key]
            input_kwargs['value'] = vd.input(**input_kwargs,
                                             attr=colors.color_edit_cell,
                                             updater=_drawPrompt,
                                             record=False,
                                             _input_rows=len(keys),
                                             bindings={
                'Shift+Tab':   change_input(-1),
                'Tab':     change_input(+1),
                'Shift+Up':   change_input(-1),
                'Shift+Down': change_input(+1),
            })
            break
        except ChangeInput as e:
            input_kwargs['value'] = e.args[0]
            offset = e.args[1]
            i = keys.index(cur_input_key)
            cur_input_key = keys[(i+offset)%len(keys)]

    retargs = {}
    lastargs = {}
    for k, input_kwargs in kwargs.items():
        v = input_kwargs.get('value', '')
        retargs[k] = v

        if input_kwargs.get('record', record):
            if input_kwargs.get('display', True):
                lastargs[k] = v
                vd.addInputHistory(v, input_kwargs.get('type', ''))
    if record:
        if vd.cmdlog and lastargs:
            vd.setLastArgs(lastargs)

    return retargs


@VisiData.api
def input(vd, prompt, type=None, defaultLast=False, history=[], dy=0, attr=None, updater=lambda v: None, **kwargs):
    '''Display *prompt* and return line of user input.

        - *type*: string indicating the type of input to use for history.
        - *history*: list of strings to use for input history.
        - *defaultLast*:  on empty input, if True, return last history item.
        - *display*: pass False to not display input (for sensitive input, e.g. a password), and to also prevent recording input as if *record* is False
        - *record*: pass False to not record input on cmdlog or input history (for sensitive or inconsequential input).
        - *completer*: ``completer(val, idx)`` is called on TAB to get next completed value.
        - *updater*: ``updater(val)`` is called every keypress or timeout.
        - *bindings*: dict of keystroke to func(v, i) that returns updated (v, i)
        - *dy*: number of lines from bottom of pane
        - *attr*: curses attribute for prompt
        - *help*: string to include in help
    '''

    if attr is None:
        attr = ColorAttr()
    sheet = vd.activeSheet
    if not vd.cursesEnabled:
        if vd.cmdlog:
            # batch/replay mode: use replay input regardless of record flag; never read stdin
            return vd.getCommandInput()

        if kwargs.get('display', True):
            import builtins
            return builtins.input(prompt)
        else:
            import getpass
            return getpass.getpass(prompt)

    if not history:
        history = list(vd.inputHistory.setdefault(type, {}).keys())

    y = sheet.windowHeight-dy-1
    promptlen = dispwidth(prompt)

    def _drawPrompt(val=''):
        rstatuslen = vd.drawRightStatus(sheet._scr, sheet)
        clipdraw(sheet._scr, y, 0, prompt, attr, w=sheet.windowWidth-rstatuslen-1)
        updater(val)
        return sheet.windowWidth-promptlen-rstatuslen-2

    w = kwargs.pop('w', _drawPrompt())
    restarts = 0
    while restarts < 100:
        #recalculate y to handle resize events
        y = sheet.windowHeight-dy-1
        try:
            ret = vd.editText(y, promptlen, w=w,
                                attr=colors.color_edit_cell,
                                options=vd.options,
                                history=history,
                                updater=_drawPrompt,
                                **kwargs)
            if ret:
                if kwargs.get('record', True) and kwargs.get('display', True):
                    vd.addInputHistory(ret, type=type)
            elif defaultLast:
                history or vd.fail("no previous input")
                ret = history[-1]

            return ret
        except curses.error:
            vd.warning('restarting input due to resize')
            restarts += 1
    # if it keeps happening, it's probably not resize events, so give some debug output
    vd.error(f'aborting input:  y={y}, w={w}, windowHeight={sheet.windowHeight}, windowWidth={sheet.windowWidth}')


@VisiData.api
def confirm(vd, prompt, exc=EscapeException):
    'Display *prompt* on status line and demand input that starts with "Y" or "y" to proceed.  Raise *exc* otherwise.  Return True.'
    if vd.options.confirm.startswith('y'):
        return True
    if vd.options.batch:
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
       - *vcolidx*: numeric index into ``self.availCols``. When None, use current column.
       - *rowidx*: numeric index into ``self.rows``.  If negative, indicates the column name in the header.
       - *value*: if given, the starting input; otherwise the starting input is the cell value or column name as appropriate.
       - *kwargs*: passthrough args to ``vd.editText``.
       '''

    if vcolidx is None:
        vcolidx = self.cursorVisibleColIndex
    x, w = self._visibleColLayout.get(vcolidx, (0, 0))

    col = self.availCols[vcolidx]

    if rowidx is None:
        rowidx = self.cursorRowIndex

    if rowidx < 0:  # header
        y = 0
        value = value or col.name
    else:
        if col.readonly:
            vd.fail('cannot edit readonly column')
        y, h = self._rowLayout.get(rowidx, (0, 0))
        value = value or col.getFullDisplayValue(self.rows[self.cursorRowIndex])

    bindings={
        'Shift+Up':     acceptThenFunc('go-up', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'Shift+Down':     acceptThenFunc('go-down', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'Shift+Right': acceptThenFunc('go-right', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'Shift+Left':  acceptThenFunc('go-left', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'Tab':         acceptThenFunc('go-right', 'rename-col' if rowidx < 0 else 'edit-cell'),
        'Shift+Tab':   acceptThenFunc('go-left', 'rename-col' if rowidx < 0 else 'edit-cell'),
    }

    if vcolidx == self.nVisibleCols-1 or vcolidx >= self.nCols-1:
        if rowidx < 0:
            bindings['Tab'] = acceptThenFunc('go-leftmost', 'rename-col')
        else:
            bindings['Tab'] = acceptThenFunc('go-down', 'go-leftmost', 'edit-cell')

    if vcolidx <= 0:
        if rowidx < 0:
            bindings['Shift+Tab'] = acceptThenFunc('go-rightmost', 'rename-col')
        else:
            bindings['Shift+Tab'] = acceptThenFunc('go-up', 'go-rightmost', 'edit-cell')

    bindings.update(vd.editCellBindings)
    # update local bindings with kwargs.bindings instead of the inverse, to preserve kwargs.bindings for caller
    bindings.update(kwargs.get('bindings', {}))
    kwargs['bindings'] = bindings

    editargs = dict(value=value, options=self.options)

    editargs.update(kwargs)  # update with user-specified args
    try:
        r = vd.editText(y, x, w, attr=colors.color_edit_cell, **editargs)
    except curses.error:
        vd.fail(f'aborting edit due to resize')

    if rowidx >= 0:  # if not header
        r = col.type(r)  # convert input to column type, let exceptions be raised

    return r


vd.addGlobals(CompleteKey=CompleteKey, AcceptInput=AcceptInput, InputWidget=InputWidget, acceptThenFunc=acceptThenFunc)
