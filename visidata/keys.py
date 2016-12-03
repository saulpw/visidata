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

def keyname(ch):
    return curses.keyname(ch).decode('utf-8')

def ctrl(ch):
    return ord(ch) & 31  # convert from 'a' to ^A keycode

ENTER = ctrl('j')
ESC = 27
