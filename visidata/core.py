
import functools
import curses

import sys
import os
import os.path
from copy import copy
import io
import collections
import functools
import statistics
import curses

import re
import csv

from .tui import edit_text, Key, Shift, Ctrl, keyname, EscapeException, wrapper, colors
from . import __version__, vdglobals
from .Path import Path

base_options = collections.OrderedDict()
user_options = None

def option(name, default, helpstr=''):
    if name not in base_options:
        base_options[name] = default

def theme(name, default, helpstr=''):
    base_options[name] = default

theme('ch_StatusSep', ' | ', 'string separating multiple statuses')
theme('ch_Unprintable', '.', 'a substitute character for unprintables')
theme('ch_ColumnFiller', ' ', 'pad chars after column value')
theme('ch_Newline', '\\n', 'displayable newline')
theme('c_StatusLine', 'bold', 'status line color')
theme('c_EditCell', 'normal', 'edit cell  line color')
theme('SheetNameFmt', '%s| ', 'status line prefix')

class attrdict(object):
    'simple class to turn a dictionary into an object with its keys as attributes'
    def __init__(self, kwargs):
        self.__dict__ = kwargs

    @classmethod
    def kwargs(cls, **kwargs):
        return cls(kwargs)

options = attrdict(base_options)


option('debug', '', 'abort on error and display stacktrace')
option('readonly', '', 'disable saving')


windowWidth = None
windowHeight = None

initialStatus = 'saul.pw/VisiData v' + __version__



def values(r, cols):
    'returns an object to access specific column values in a row by .<column_name>'
    d = {}
    for c in cols:
        d[c.name] = c.getValue(r)
    return attrdict(d)

def error(s):
    'scripty sugar function to just raise, also needed for lambda and eval'
    raise Exception(s)

def status(s):
    'scripty sugar'
    return vd().status(s)

def moveListItem(L, fromidx, toidx):
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx

# VisiData singleton contains all sheets
@functools.lru_cache()
def vd():
    return VisiData()

def exceptionCaught(status=True):
    return vd().exceptionCaught(status)

class VisiData:
    # base_commands is a list that contains the commands defined by the visidata package (including some that are sheet-specific).
    # user_commands contains all user-specified overrides.  Any changes to base_commands are actually additions to user_commands.
    # They are used by the sheet's reload_commands() to make its sheet.commands, and also serve as the sources for the gF1 SheetAppend.
    base_commands = []
    user_commands = []
    allPrefixes = 'g'

    def __init__(self):
        self.sheets = []
        self.statusHistory = []
        self._status = [initialStatus]
        self.lastErrors = []
        self.nchars = 0

    def status(self, s):
        strs = str(s)
        self._status.append(strs)
        self.statusHistory.insert(0, strs)
        del self.statusHistory[100:]  # keep most recent 100 only
        return s

    def editText(self, y, x, w, **kwargs):
        v = edit_text(self.scr, y, x, w, **kwargs)
        self.status('"%s"' % v)
        return v

    def exceptionCaught(self, status=True):
        import traceback
        self.lastErrors.append(traceback.format_exc().strip())
        self.lastErrors = self.lastErrors[-10:]  # keep most recent
        if status:
            self.status(self.lastErrors[-1].splitlines()[-1])
        if options.debug:
            raise

    def drawLeftStatus(self, sheet):
        'draws sheet info on last line, including previous status messages, which are then cleared.'
        attr = colors[options.c_StatusLine]
        statusstr = options.SheetNameFmt % sheet.name + options.ch_StatusSep.join(self._status)
        try:
            draw_clip(self.scr, windowHeight-1, 0, statusstr, attr, windowWidth)
        except Exception as e:
            self.exceptionCaught()
        self._status = []

    def drawRightStatus(self, rstatus):
        try:
            draw_clip(self.scr, windowHeight-1, windowWidth-len(rstatus)-2, rstatus, colors[options.c_StatusLine])
        except Exception as e:
            self.exceptionCaught()

    def run(self, scr):
        global windowHeight, windowWidth, sheet
        windowHeight, windowWidth = scr.getmaxyx()
        self.scr = scr

        command_overrides = None
        prefixes = ''
        keystroke = ''
        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]
            if sheet.nRows == 0:
                self.status('no rows')

            try:
                sheet.draw(scr)
            except Exception as e:
                self.exceptionCaught()

            self.drawRightStatus(prefixes+keystroke)  # visible for this getch
            self.drawLeftStatus(sheet)

            curses.doupdate()
            ch = scr.getch()
            self.nchars += 1
            keystroke = keyname(ch)
            self.drawRightStatus(prefixes+keystroke)  # visible for commands that wait with getch
            if ch == curses.KEY_RESIZE:
                windowHeight, windowWidth = scr.getmaxyx()
            elif ch == curses.KEY_MOUSE:
                try:
                    devid, x, y, z, bstate = curses.getmouse()
                    sheet.cursorRowIndex = sheet.topRowIndex+y-1
                except Exception:
                    self.exceptionCaught()
            elif keystroke in self.allPrefixes:
                prefixes += keystroke
            else:
                try:
                    sheet.exec_command(vdglobals(), prefixes + keystroke)
                except EscapeException as e:  # user aborted
                    self.status(keyname(e.args[0]))
                except Exception:
                    self.exceptionCaught()
#                    self.status(sheet.commands[prefixes+keystroke].execstr)
                prefixes = ''

            sheet.checkCursor()

    def replace(self, vs):
        'replace top sheet with the given sheet'
        self.sheets.pop(0)
        return vs.push(vs)

    def push(self, vs):
        if vs:
            if vs in self.sheets:
                self.sheets.remove(vs)
            elif not vs.rows:  # first time
                vs.reload_commands()
                vs.reload()
            self.sheets.insert(0, vs)
            return vs
# end VisiData class

def inputLine(prompt, value='', completions=None):
    'add a prompt to the bottom of the screen and get a line of input from the user'
    scr = vd().scr
    windowHeight, windowWidth = scr.getmaxyx()
    scr.addstr(windowHeight-1, 0, prompt)
    return vd().editText(windowHeight-1, len(prompt), windowWidth-len(prompt)-8, value=value, attr=colors[options.c_EditCell], unprintablechar=options.ch_Unprintable, completions=completions)

option('SubsheetSep', '~')
def join_sheetnames(*sheetnames):
    return options.SubsheetSep.join(str(x) for x in sheetnames)


option('save_dir', '.', 'default output folder')
def saveSheet(sheet, fn):
    if options.readonly:
        status('readonly mode')
        return
    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in vdglobals():
        funcname = 'save_tsv'
    vdglobals().get(funcname)(sheet, fn)
    status('saved to ' + fn)


def draw_clip(scr, y, x, s, attr=curses.A_NORMAL, w=None):
    'Draw string s at (y,x)-(y,x+w), clipping with ellipsis char'
    s = s.replace('\n', options.ch_Newline)

    _, windowWidth = scr.getmaxyx()
    try:
        if w is None:
            w = windowWidth-1
        w = min(w, windowWidth-x-1)
        if w == 0:  # no room anyway
            return

        # convert to string just before drawing
        s = str(s)
        if len(s) > w:
            scr.addstr(y, x, s[:w-1] + options.ch_Ellipsis, attr)
        else:
            scr.addstr(y, x, s, attr)
            if len(s) < w:
                scr.addstr(y, x+len(s), options.ch_ColumnFiller*(w-len(s)), attr)
    except Exception as e:
        raise type(e)('%s [clip_draw y=%s x=%s len(s)=%s w=%s]' % (e, y, x, len(s), w)
                ).with_traceback(sys.exc_info()[2])

