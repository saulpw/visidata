import contextlib
import os
import curses
import threading
import time

from visidata import vd, VisiData, colors, bindkeys, ESC

curses_timeout = 100 # curses timeout in ms
timeouts_before_idle = 10


@VisiData.api
def draw(self, scr, sheet):
    'Redraw full screen.'

    scr.erase()  # clear screen before every re-draw

    sheet._scr = scr
    vd.scr = scr

    self.drawLeftStatus(scr, sheet)
    self.drawRightStatus(scr, sheet)  # visible during this getkeystroke

    try:
        sheet.draw(scr)
    except Exception as e:
        self.exceptionCaught(e)


@VisiData.api
def run(self, scr):
    'Manage execution of keystrokes and subsequent redrawing of screen.'
    scr.timeout(curses_timeout)
    with contextlib.suppress(curses.error):
        curses.curs_set(0)

    self._scr = scr
    numTimeouts = 0
    prefixWaiting = False

    self.keystrokes = ''
    while True:
        if not self.sheets:
            # if no more sheets, exit
            return

        sheet = self.sheets[0]
        threading.current_thread().sheet = sheet
        vd.drawThread = threading.current_thread()

        sheet.ensureLoaded()

        scr.erase()  # clear screen before every re-draw
        self.draw(scr, sheet)

        keystroke = self.getkeystroke(scr, sheet)

        if not keystroke and prefixWaiting and ESC in self.keystrokes:  # timeout ESC
            self.keystrokes = ''

        if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
            numTimeouts = 0
            if not prefixWaiting:
                self.keystrokes = ''

            self.statuses.clear()

            if keystroke == 'KEY_MOUSE':
                self.keystrokes = ''
                clicktype = ''
                try:
                    devid, x, y, z, bstate = curses.getmouse()
                    sheet.mouseX, sheet.mouseY = x, y
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

                    f = self.getMouse(scr, x, y, keystroke)
                    if f:
                        if isinstance(f, str):
                            for cmd in f.split():
                                sheet.exec_keystrokes(cmd)
                        else:
                            f(y, x, keystroke)

                        self.keystrokes = keystroke
                        keystroke = ''
                except curses.error:
                    pass
                except Exception as e:
                    exceptionCaught(e)

            if keystroke in self.keystrokes[:-1]:
                vd.warning('duplicate prefix')
                self.keystrokes = ''
            else:
                self.keystrokes += keystroke

        self.drawRightStatus(sheet._scr, sheet)  # visible for commands that wait for input

        if not keystroke:  # timeout instead of keypress
            pass
        elif keystroke == '^Q':
            return self.lastErrors and '\n'.join(self.lastErrors[-1])
        elif bindkeys._get(self.keystrokes):
            sheet.exec_keystrokes(self.keystrokes)
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
            scr.timeout(curses_timeout)
        else:
            numTimeouts += 1
            if numTimeouts > timeouts_before_idle:
                scr.timeout(-1)
            else:
                scr.timeout(curses_timeout)


def setupcolors(stdscr, f, *args):
    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"
    curses.mousemask(-1) # even more than curses.ALL_MOUSE_EVENTS
    curses.mouseinterval(0) # very snappy but does not allow for [multi]click
    curses.mouseEvents = {}

    for k in dir(curses):
        if k.startswith('BUTTON') or k == 'REPORT_MOUSE_POSITION':
            curses.mouseEvents[getattr(curses, k)] = k

    return f(stdscr, *args)

def wrapper(f, *args):
    return curses.wrapper(setupcolors, f, *args)

def run(*sheetlist):
    'Main entry point; launches vdtui with the given sheets already pushed (last one is visible)'

    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    curses.use_env(True)

    ret = wrapper(cursesMain, sheetlist)

    if ret:
        print(ret)

def cursesMain(_scr, sheetlist):
    'Populate VisiData object with sheets from a given list.'

    colors.setup()

    for vs in sheetlist:
        vd.push(vs)

    vd.status('Ctrl+H opens help')
    return vd.run(_scr)
