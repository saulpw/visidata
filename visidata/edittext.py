# Copyright (C) 2016 Saul Pwanson
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import curses
from curses.ascii import DEL

from .exceptions import VEscape
from .keys import ctrl, ENTER, ESC, keyname
from .options import colors, options


### curses, options, init
def editText(vd, scr, y, x, w, prompt='', value='', fillchar=' '):
    def splice(v, i, s):  # splices s into the string v at i (v[i] = s[0])
        return v if i < 0 else v[:i] + s + v[i:]
    def clean(s):
        return ''.join(c if c.isprintable() else options.Unprintable for c in s)
    def delchar(s, i, remove=1):
        return s[:i] + s[i+remove:]

    if prompt:
        scr.addstr(y, x, prompt)
        x += len(prompt)
        w -= len(prompt)

    v = value   # value under edit
    i = 0       # index into v
    while True:
        dispval = clean(v)
        dispi = i
        if len(v) < w:
            dispval += fillchar*(w-len(v))
        elif i >= w:
            dispi = w-1
            dispval = dispval[i-w:]

        scr.addstr(y, x, dispval, colors[options.c_EditCell])
        scr.move(y, x+dispi)
        ch = scr.getch()
        if ch == ctrl('a') or ch == curses.KEY_HOME:        i = 0
        elif ch == ctrl('b') or ch == curses.KEY_LEFT:      i -= 1
        elif ch == ctrl('c') or ch == ESC:                  raise VEscape(keyname(ch))
        elif ch == ctrl('d') or ch == curses.KEY_DC:        v = delchar(v, i)
        elif ch == ctrl('e') or ch == curses.KEY_END:       i = len(v)
        elif ch == ctrl('f') or ch == curses.KEY_RIGHT:     i += 1
        elif ch in (ctrl('h'), curses.KEY_BACKSPACE, DEL):  i -= 1 if i > 0 else 0; v = delchar(v, i)
        elif ch == ctrl('j') or ch == ENTER:                break
        elif ch == ctrl('k'):                               v = v[:i]
        elif ch == ctrl('r'):                               v = value
        elif ch == ctrl('t'):                               v = delchar(splice(v, i-2, v[i-1]), i)
        elif ch == ctrl('u'):                               v = v[i:]; i = 0
        elif ch == ctrl('v'):                               v = splice(v, i, chr(scr.getch())); i+= 1
        else:
            v = splice(v, i, chr(ch))
            i += 1

        if i < 0: i = 0
        if i > len(v): i = len(v)

    vd.status('"%s"' % v)
    return v
