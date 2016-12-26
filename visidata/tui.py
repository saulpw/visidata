
import sys
import collections
import curses
import curses.ascii

colors = collections.defaultdict(lambda: curses.A_NORMAL, {
    'bold': curses.A_BOLD,
    'reverse': curses.A_REVERSE,
    'normal': curses.A_NORMAL,
})


class EscapeException(Exception):
    pass


class CtrlKey(object):
    def __getattr__(self, k):  # Ctrl.a or Ctrl.A -> ^A keycode
        return ord(k) & 31

    def __call__(self, k):   # ctrl('^') -> Ctrl-^ keycode
        return ord(k) & 31
Ctrl = CtrlKey()


class ShiftKey(object):
    def __getattr__(self, k):  # Ctrl.a or Ctrl.A -> ^A keycode
        assert curses.ascii.isupper(k)
        return ord(k)
Shift = ShiftKey()


class PlainKey(object):
    TAB = Ctrl.I
    ENTER = Ctrl.J
    ESC = 27
    DEL = curses.ascii.DEL

    def __getattr__(self, k):
        if len(k) == 1 and ord(k) < 127:
            return ord(k)
        return getattr(curses, 'KEY_' + k)

    def __call__(self, k):
        assert len(k) == 1 and ord(k) < 127
        return ord(k)
Key = PlainKey()


def keyname(ch):
    return curses.keyname(ch).decode('utf-8')


def edit_text(scr, y, x, w, attr=curses.A_NORMAL, value='', fillchar=' ', unprintablechar='.', completions=[]):
    def splice(v, i, s):  # splices s into the string v at i (v[i] = s[0])
        return v if i < 0 else v[:i] + s + v[i:]

    def clean(s):
        return ''.join(c if c.isprintable() else unprintablechar for c in str(s))

    def delchar(s, i, remove=1):
        return s[:i] + s[i+remove:]

    def complete(v, comps, cidx):
        if comps:
            for i in range(cidx, cidx + len(comps)):
                i %= len(comps)
                if comps[i].startswith(v):
                    return comps[i]
        # beep
        return v

    insert_mode = False
    v = str(value)  # value under edit
    i = 0           # index into v
    comps_idx = 2

    while True:
        dispval = clean(v)
        dispi = i
        if len(dispval) < w:
            dispval += fillchar*(w-len(dispval))
        elif i >= w:
            dispi = w-1
            dispval = dispval[i-w:]

        scr.addstr(y, x, dispval, attr)
        scr.move(y, x+dispi)
        ch = scr.getch()
        if ch == Key.IC:                             insert_mode = not insert_mode
        elif ch == Ctrl.A or ch == Key.HOME:         i = 0
        elif ch == Ctrl.B or ch == Key.LEFT:         i -= 1
        elif ch == Ctrl.C or ch == Key.ESC:          raise EscapeException(ch)
        elif ch == Ctrl.D or ch == Key.DC:           v = delchar(v, i)
        elif ch == Ctrl.E or ch == Key.END:          i = len(v)
        elif ch == Ctrl.F or ch == Key.RIGHT:        i += 1
        elif ch in (Ctrl.H, Key.BACKSPACE, Key.DEL): i -= 1 if i > 0 else 0; v = delchar(v, i)
        elif ch == Key.TAB:                          comps_idx += 1; v = complete(v[:i], completions, comps_idx)
        elif ch == Key.BTAB:                         comps_idx -= 1; v = complete(v[:i], completions, comps_idx)
        elif ch == Ctrl.J or ch == Key.ENTER:        break
        elif ch == Ctrl.K:                           v = v[:i]
        elif ch == Ctrl.R:                           v = value
        elif ch == Ctrl.T:                           v = delchar(splice(v, i-2, v[i-1]), i)
        elif ch == Ctrl.U:                           v = v[i:]; i = 0
        elif ch == Ctrl.V:                           v = splice(v, i, chr(scr.getch())); i += 1
        else:
            if insert_mode:
                v = splice(v, i, chr(ch))
            else:
                v = v[:i] + chr(ch) + v[i+1:]

            i += 1

        if i < 0: i = 0
        if i > len(v): i = len(v)

    return v


nextColorPair = 1
def setupcolors(stdscr, f, *args):
    def makeColor(fg, bg):
        global nextColorPair
        if curses.has_colors():
            curses.init_pair(nextColorPair, fg, bg)
            c = curses.color_pair(nextColorPair)
            nextColorPair += 1
        else:
            c = curses.A_NORMAL

        return c

    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"
#    curses.mousemask(curses.ALL_MOUSE_EVENTS)  # enable mouse events

    colors['red'] = curses.A_BOLD | makeColor(curses.COLOR_RED, curses.COLOR_BLACK)
    colors['blue'] = curses.A_BOLD | makeColor(curses.COLOR_BLUE, curses.COLOR_BLACK)
    colors['green'] = curses.A_BOLD | makeColor(curses.COLOR_GREEN, curses.COLOR_BLACK)
    colors['brown'] = makeColor(curses.COLOR_YELLOW, curses.COLOR_BLACK)
    colors['yellow'] = curses.A_BOLD | colors['brown']
    colors['cyan'] = makeColor(curses.COLOR_CYAN, curses.COLOR_BLACK)
    colors['magenta'] = makeColor(curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    colors['red_bg'] = makeColor(curses.COLOR_WHITE, curses.COLOR_RED)
    colors['blue_bg'] = makeColor(curses.COLOR_WHITE, curses.COLOR_BLUE)
    colors['green_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_GREEN)
    colors['brown_bg'] = colors['yellow_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_YELLOW)
    colors['cyan_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_CYAN)
    colors['magenta_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_MAGENTA)

    return f(stdscr, *args)


def wrapper(f, *args):
    return curses.wrapper(setupcolors, f, *args)
