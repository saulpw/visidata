import contextlib
import os
import curses
import signal
import threading
import time
from unittest import mock

from visidata import vd, VisiData, colors, ESC, options, clipbox

__all__ = ['ReturnValue', 'run']

vd.curses_timeout = 100 # curses timeout in ms
vd.timeouts_before_idle = 10

vd.option('disp_splitwin_pct', 0, 'height of second sheet on screen')
vd.option('mouse_interval', 1, 'max time between press/release for click (ms)', sheettype=None)
vd.option('color_sidebar', 'black on 114 blue', 'color of sidebar')


class ReturnValue(BaseException):
    'raise ReturnValue(ret) to exit from an inner runresult() with its result.'
    pass



@VisiData.api
def draw_sheet(self, scr, sheet):
    'Erase *scr* and draw *sheet* on it, including status bars and sidebar.'

    sheet.ensureLoaded()

    scr.erase()  # clear screen before every re-draw
    scr.bkgd(' ', colors.color_default)

    sheet._scr = scr

    self.drawLeftStatus(scr, sheet)
    self.drawRightStatus(scr, sheet)  # visible during this getkeystroke

    try:
        sheet.draw(scr)
    except Exception as e:
        self.exceptionCaught(e)

    try:
        vd.drawSidebar(scr, sheet.sidebar)
    except Exception as e:
        vd.exceptionCaught(e)


def iterwraplines(lines, width=80):
    import textwrap
    for line in lines:
        yield from textwrap.wrap(line, width=width, subsequent_indent='  ')


@VisiData.api
def drawSidebar(vd, scr, text, title='sidebar'):
    if not text:
        return

    h, w = scr.getmaxyx()
    maxh, maxw = 0, 0

    lines = list(iterwraplines(text.splitlines(), width=w//2))

    maxh = min(h-2, len(lines)+2)
    maxw = min(w//2, max(map(len, lines))+4)

    sidebar_scr = scr.derwin(maxh, maxw, h-maxh-1, w-maxw-1)
    clipbox(sidebar_scr, lines, colors.color_sidebar, title=title)


vd.windowConfig = dict(pct=0, n=0, h=0, w=0)  # n=top line of bottom window; h=height of bottom window; w=width of screen
vd.winTop = mock.MagicMock(__bool__=mock.Mock(return_value=False))
vd.scrMenu = mock.MagicMock(__bool__=mock.Mock(return_value=False))

@VisiData.api
def setWindows(vd, scr, pct=None):
    'Assign winTop, winBottom, win1 and win2 according to options.disp_splitwin_pct.'
    if pct is None:
        pct = options.disp_splitwin_pct  # percent of window for secondary sheet (negative means bottom)
    disp_menu = vd.menuRunning or vd.options.disp_menu
    topmenulines = 1 if disp_menu else 0
    h, w = scr.getmaxyx()

    n = 0
    if pct:
        # on 100 line screen, pct = 25 means second window on lines 75-100.  pct -25 -> lines 0-25
        n = abs(pct)*h//100
        n = min(n, h-topmenulines-3)
        n = max(3, n)

    desiredConfig = dict(pct=pct, n=n, h=h-topmenulines, w=w)

    if vd.scrFull is not scr or vd.windowConfig != desiredConfig:
        if not topmenulines:
            vd.scrMenu = None
        elif not vd.scrMenu:
            vd.scrMenu = scr.derwin(h, w, 0, 0)
            vd.scrMenu.keypad(1)

        vd.winTop = scr.derwin(n, w, topmenulines, 0)
        vd.winTop.keypad(1)
        vd.winBottom = scr.derwin(h-n-topmenulines, w, n+topmenulines, 0)
        vd.winBottom.keypad(1)
        if pct == 0 or pct >= 100:  # no second pane
            vd.win1 = vd.winBottom
            # drawing to 0-line window causes problems
            vd.win2 = mock.MagicMock(__bool__=mock.Mock(return_value=False))
        elif pct > 0: # pane 2 from line n to bottom
            vd.win1 = vd.winTop
            vd.win2 = vd.winBottom
        elif pct < 0: # pane 2 from line 0 to n
            vd.win1 = vd.winBottom
            vd.win2 = vd.winTop

        for vs in vd.sheetstack(1)[0:1]+vd.sheetstack(2)[0:1]:
            vs.refresh()

        vd.windowConfig = desiredConfig
        vd.scrFull = scr
        return True


@VisiData.api
def draw_all(vd):
    'Draw all sheets in all windows.'
    vd.clearCaches()

    ss1 = vd.sheetstack(1)
    ss2 = vd.sheetstack(2)
    if ss1 and not ss2:
        vd.activePane = 1
        vd.setWindows(vd.scrFull)
        vd.draw_sheet(vd.win1, ss1[0])
        if vd.win2:
            vd.win2.erase()
    elif not ss1 and ss2:
        vd.activePane = 2
        vd.setWindows(vd.scrFull)
        vd.draw_sheet(vd.win2, ss2[0])
        if vd.win1:
            vd.win1.erase()
    elif ss1 and ss2 and vd.win2:
        vd.draw_sheet(vd.win1, ss1[0])
        vd.draw_sheet(vd.win2, ss2[0])
    elif ss1 and ss2 and not vd.win2:
        vd.draw_sheet(vd.win1, vd.sheetstack(vd.activePane)[0])
        vd.setWindows(vd.scrFull)

    if vd.scrMenu:
        vd.drawMenu(vd.scrMenu, vd.activeSheet)

    if vd.win1:
        vd.win1.refresh()
    if vd.win2:
        vd.win2.refresh()
    if vd.scrMenu:
        vd.scrMenu.refresh()


@VisiData.api
def runresult(vd):
    try:
        err = vd.mainloop(vd.scrFull)
        if err:
            raise Exception(err)
    except ReturnValue as e:
        return e.args[0]


@VisiData.api
def parseMouse(vd, **kwargs):
    devid, x, y, z, bstate = curses.getmouse()

    found = False
    for winname, winscr in kwargs.items():
        py, px = winscr.getparyx()
        mh, mw = winscr.getmaxyx()
        if py <= y < py+mh and px <= x < px+mw:
            y, x, = y-py, x-px
            found = True
            # vd.status('clicked at (%s, %s) in %s' % (y, x, winname))
            break

    clicktype = ''
    if bstate & curses.BUTTON_CTRL:
        clicktype += "CTRL-"
        bstate &= ~curses.BUTTON_CTRL
    if bstate & curses.BUTTON_ALT:
        clicktype += "ALT-"
        bstate &= ~curses.BUTTON_ALT
    if bstate & curses.BUTTON_SHIFT:
        clicktype += "SHIFT-"
        bstate &= ~curses.BUTTON_SHIFT

    keystroke = clicktype + curses.mouseEvents.get(bstate, str(bstate))

    if found:
        return keystroke, y, x, winname, winscr

    return keystroke, y, x, "whatwin", None


@VisiData.api
def mainloop(self, scr):
    'Manage execution of keystrokes and subsequent redrawing of screen.'
    scr.timeout(vd.curses_timeout)
    with contextlib.suppress(curses.error):
        curses.curs_set(0)

    numTimeouts = 0
    prefixWaiting = False
    vd.scrFull = scr

    self.keystrokes = ''
    while True:
        if not self.stackedSheets and self.currentReplay is None:
            return

        sheet = self.activeSheet

        if not sheet:
            continue

        threading.current_thread().sheet = sheet
        vd.drawThread = threading.current_thread()

        vd.setWindows(vd.scrFull)

        self.draw_all()

        if vd._nextCommands:
            sheet.execCommand(vd._nextCommands.pop(0), keystrokes=self.keystrokes)
            continue

        keystroke = self.getkeystroke(scr, sheet)

        if not keystroke and prefixWaiting and "Alt+" in self.keystrokes:  # timeout ESC
            self.keystrokes = ''

        if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
            numTimeouts = 0
            if not prefixWaiting:
                self.keystrokes = ''

            self.statuses.clear()

            if keystroke == 'KEY_MOUSE':
                self.keystrokes = ''
                keystroke, y, x, winname, winscr = vd.parseMouse(top=vd.winTop, bot=vd.winBottom, menu=vd.scrMenu)

                pct = vd.windowConfig['pct']
                topPaneActive = ((vd.activePane == 2 and pct < 0)  or (vd.activePane == 1 and pct > 0))
                bottomPaneActive = ((vd.activePane == 1 and pct < 0)  or (vd.activePane == 2 and pct > 0))

                if (bottomPaneActive and winname == 'top') or (topPaneActive and winname == 'bot'):
                    self.activePane = 1 if self.activePane == 2 else 2
                    sheet = self.activeSheet

                try:
                    f = self.getMouse(winscr, x, y, keystroke)
                    sheet.mouseX, sheet.mouseY = x, y
                    if f:
                        if isinstance(f, str):
                            for cmd in f.split():
                                sheet.execCommand(cmd)
                        else:
                            f(y, x, keystroke)

                        self.keystrokes = self.prettykeys(keystroke)
                        keystroke = ''   # already handled
                except curses.error:
                    pass
                except Exception as e:
                    self.exceptionCaught(e)

            if keystroke and keystroke in self.keystrokes[:-1]:
                vd.warning('duplicate prefix: ' + keystroke)
                self.keystrokes = ''
            else:
                self.keystrokes += self.prettykeys(keystroke)

        self.drawRightStatus(sheet._scr, sheet)  # visible for commands that wait for input

        if not keystroke:  # timeout instead of keypress
            pass
        elif keystroke == '^Q':
            return self.lastErrors and '\n'.join(self.lastErrors[-1])
        elif vd.bindkeys._get(self.keystrokes):
            sheet.execCommand(self.keystrokes, keystrokes=self.keystrokes)
            prefixWaiting = False
        elif keystroke in self.allPrefixes:
            prefixWaiting = True
        else:
            vd.status('no command for "%s"' % (self.keystrokes))
            prefixWaiting = False

        self.checkForFinishedThreads()
        sheet.checkCursorNoExceptions()

        # no idle redraw unless background threads are running
        time.sleep(0)  # yield to other threads which may not have started yet
        if vd.unfinishedThreads:
            scr.timeout(vd.curses_timeout)
        else:
            numTimeouts += 1
            if vd.timeouts_before_idle >= 0 and numTimeouts > vd.timeouts_before_idle:
                scr.timeout(-1)
            else:
                scr.timeout(vd.curses_timeout)


def initCurses():
    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')
    curses.use_env(True)

    scr = curses.initscr()

    curses.start_color()

    colors.setup()

    curses.noecho()

    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"
    curses.MOUSE_ALL = 0xffffffff
    curses.mousemask(curses.MOUSE_ALL if options.mouse_interval else 0)
    curses.mouseinterval(options.mouse_interval)
    curses.mouseEvents = {}

    scr.keypad(1)

    curses.def_prog_mode()

    for k in dir(curses):
        if k.startswith('BUTTON') or k in ('REPORT_MOUSE_POSITION', '2097152'):
            curses.mouseEvents[getattr(curses, k)] = k

    return scr


def wrapper(f, *args, **kwargs):
    try:
        scr = initCurses()
        return f(scr, *args, **kwargs)
    finally:
        curses.endwin()


@VisiData.global_api
def run(vd, *sheetlist):
    'Main entry point; launches vdtui with the given sheets already pushed (last one is visible)'

    scr = None
    try:
        # Populate VisiData object with sheets from a given list.
        for vs in sheetlist:
            vd.push(vs)

        scr = initCurses()
        ret = vd.mainloop(scr)
    except curses.error as e:
        vd.fail(str(e))
    finally:
        if scr:
            curses.endwin()

    vd.cancelThread(*[t for t in vd.unfinishedThreads if not t.name.startswith('save_')])

    if ret:
        print(ret)
