import builtins
import contextlib
import os
import curses
import signal
import threading
import time

from visidata import vd, VisiData, colors, ESC, options, BaseSheet, AttrDict

__all__ = ['ReturnValue', 'run']

vd.curses_timeout = 100 # curses timeout in ms
vd.timeouts_before_idle = 10
vd.min_draw_ms = 100  # draw_all at least this often, even if keystrokes are pending
vd._lastDrawTime = 0  # last time drawn (from time.time())


class ReturnValue(BaseException):
    'raise ReturnValue(ret) to exit from an inner runresult() with its result.'
    pass


@VisiData.api
def callNoExceptions(vd, func, *args, **kwargs):
    'Catch and log any raised exceptions.  Reraise when options.debug.'
    try:
        return func(*args, **kwargs)
    except Exception as e:
        vd.exceptionCaught(e)


@VisiData.api
def drawSheet(vd, scr, sheet):
    'Erase *scr* and draw *sheet* on it, including status bars and sidebar.'

    sheet.ensureLoaded()

    if not scr:
        return

    scr.erase()  # clear screen before every re-draw
    scr.bkgd(' ', colors.color_default.attr)

    sheet._scr = scr

    vd.callNoExceptions(sheet.draw, scr)
    vd.callNoExceptions(vd.drawLeftStatus, scr, sheet)
    vd.callNoExceptions(vd.drawRightStatus, scr, sheet)  # visible during this getkeystroke


vd.windowConfig = dict(pct=0, n=0, h=0, w=0)  # n=top line of bottom window; h=height of bottom window; w=width of screen

vd.winTop = None
vd.scrMenu = None
vd.scrFull = None


@VisiData.api
def setWindows(vd, scr, pct=None):
    'Assign winTop, winBottom, win1 and win2 according to options.disp_splitwin_pct.'
    if pct is None:
        pct = options.disp_splitwin_pct  # percent of window for secondary sheet (negative means bottom)
    disp_menu = getattr(vd, 'menuRunning', None) or vd.options.disp_menu
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
            vd.scrMenu = vd.subwindow(scr, 0, 0, w, h)
            vd.scrMenu.keypad(1)

        vd.winTop = vd.subwindow(scr, 0, topmenulines, w, n)
        vd.winTop.keypad(1)
        vd.winBottom = vd.subwindow(scr, 0, n+topmenulines, w, h-n-topmenulines)
        vd.winBottom.keypad(1)
        if pct == 0 or pct >= 100:  # no second pane
            vd.win1 = vd.winBottom
            # drawing to 0-line window causes problems
            vd.win2 = None
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
        vd.drawSheet(vd.win1, ss1[0])
        if vd.win2:
            vd.win2.erase()
    elif not ss1 and ss2:
        vd.activePane = 2
        vd.setWindows(vd.scrFull)
        vd.drawSheet(vd.win2, ss2[0])
        if vd.win1:
            vd.win1.erase()
    elif ss1 and ss2 and vd.win2:
        vd.drawSheet(vd.win1, ss1[0])
        vd.drawSheet(vd.win2, ss2[0])
    elif ss1 and ss2 and not vd.win2:
        vd.drawSheet(vd.win1, vd.sheetstack(vd.activePane)[0])
        vd.setWindows(vd.scrFull)

    if vd.scrMenu:
        vd.callNoExceptions(vd.drawMenu, vd.scrMenu, vd.activeSheet)

    vd.callNoExceptions(vd.drawSidebar, vd.scrFull, vd.activeSheet)

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
def mainloop(vd, scr):
    'Manage execution of keystrokes and subsequent redrawing of screen.'
    nonidle_timeout = vd.curses_timeout

    scr.timeout(vd.curses_timeout)
    with contextlib.suppress(curses.error):
        curses.curs_set(0)

    numTimeouts = 0
    prefixWaiting = False
    vd.scrFull = scr
    if vd.options.disp_expert >= 5:
        vd.disp_help = -1

    vd.keystrokes = ''
    vd.drawThread = threading.current_thread()
    while True:
        if not vd.stackedSheets and vd.currentReplay is None:
            return

        sheet = vd.activeSheet

        if not sheet:
            continue  # waiting for replay to push sheet

        threading.current_thread().sheet = sheet

        vd.setWindows(vd.scrFull)

        # a newly created sheet needs to be drawn once to set its _scr
        if vd.activeSheet._scr is None or \
           not vd.drainPendingKeys(scr) or \
           time.time() - vd._lastDrawTime > vd.min_draw_ms/1000:  #1459
            vd.draw_all()
            vd._lastDrawTime = time.time()

        keystroke = vd.getkeystroke(scr, sheet)

        if not keystroke and prefixWaiting and "Alt+" in vd.keystrokes:  # timeout ESC
            vd.keystrokes = ''

        if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
            numTimeouts = 0
            if not prefixWaiting:
                vd.keystrokes = ''

            vd.statuses.clear()

            if keystroke == 'KEY_MOUSE':
                try:
                    keystroke = vd.handleMouse(sheet)  # if it was handled, don't handle again as a regular keystroke
                except Exception as e:
                    vd.exceptionCaught(e)

            if keystroke and keystroke in vd.allPrefixes and keystroke in vd.keystrokes[:-1]:
                vd.warning('duplicate prefix: ' + keystroke)
                vd.keystrokes = ''
            else:
                vd.keystrokes += keystroke

        vd.drawRightStatus(sheet._scr, sheet)  # visible for commands that wait for input

        if not keystroke:  # timeout instead of keypress
            pass
        elif keystroke == 'Ctrl+Q':
            return vd.lastErrors and '\n'.join(vd.lastErrors[-1])
        elif vd.bindkeys._get(vd.keystrokes) is not None:
            sheet.execCommand(vd.keystrokes, keystrokes=vd.keystrokes)
            prefixWaiting = False
        elif vd.keystrokes in vd.allPrefixes:
            prefixWaiting = True
        else:
            vd.status('no command for "%s"' % (vd.keystrokes))
            prefixWaiting = False

        # play next queued command
        if vd._nextCommands and not vd.unfinishedThreads:
            cmd = vd._nextCommands.pop(0)
            if isinstance(cmd, (dict, list)):  # .vd cmdlog rows are NamedListTemplate
                try:
                    if vd.replayOne(cmd):
                        vd.replay_cancel()
                except Exception as e:
                    vd.exceptionCaught(e)
                    vd.replay_cancel()
            else:
                sheet.execCommand(cmd, keystrokes=vd.keystrokes)

        if not vd._nextCommands:
            if vd.currentReplay:
                vd.currentReplayRow = None
                vd.currentReplay = None

        vd.checkForFinishedThreads()
        vd.callNoExceptions(sheet.checkCursor)

        # no idle redraw unless background threads are running
        time.sleep(0)  # yield to other threads which may not have started yet
        if vd._nextCommands:
            if vd.options.replay_wait > 0:
                vd.curses_timeout = int(vd.options.replay_wait*1000)
            else:
                vd.curses_timeout = nonidle_timeout
        elif vd.unfinishedThreads:
            vd.curses_timeout = nonidle_timeout
        else:
            numTimeouts += 1
            if vd.timeouts_before_idle >= 0 and numTimeouts >= vd.timeouts_before_idle:
                vd.curses_timeout = -1
            else:
                vd.curses_timeout = nonidle_timeout

        scr.timeout(vd.curses_timeout)


@VisiData.api
def initCurses(vd):
    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')
    curses.use_env(True)

    scr = curses.initscr()

    curses.start_color()

    colors.setup()

    curses.noecho()

    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"

    scr.keypad(1)

    curses.def_prog_mode()

    vd.drainPendingKeys(scr)
    if '\x1b' in vd.pendingKeys:  #1993
        # if start of an ANSI escape sequence, might be mangled, discard remaining keystrokes
        vd.pendingKeys.clear()
        curses.flushinp()

    return scr


def wrapper(f, *args, **kwargs):
    try:
        scr = vd.initCurses()
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
            vd.push(vs, load=False)

        scr = vd.initCurses()
        ret = vd.mainloop(scr)
    except curses.error as e:
        if vd.options.debug:
            raise
        vd.fail(str(e))
    finally:
        if scr:
            curses.endwin()

    vd.cancelThread(*[t for t in vd.unfinishedThreads if not t.name.startswith('save_')])

    if ret:
        builtins.print(ret)

    return ret

@VisiData.api
def addCommand(vd, *args, **kwargs):
    return BaseSheet.addCommand(*args, **kwargs)


import sys
vd.addGlobals({k:getattr(sys.modules[__name__], k) for k in __all__})
