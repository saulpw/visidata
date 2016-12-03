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

colors = {
    'bold': curses.A_BOLD,
    'reverse': curses.A_REVERSE,
    'normal': curses.A_NORMAL,
}

default_options = {
    'csv_dialect': 'excel',
    'csv_delimiter': ',',
    'csv_quotechar': '"',
    'csv_header': False,

    'debug': False,
    'readonly': False,

    'encoding': 'utf-8',
    'encoding_errors': 'surrogateescape',

    'VisibleNone': '',   # visible contents of a cell whose value was None
    'ColumnFiller': ' ',
    'ColumnSep': ' | ',  # chars between columns
    'Ellipsis': '…',
    'SubsheetSep': '~',
    'StatusSep': ' | ',
    'KeySep': '/',
    'SheetNameFmt': '%s| ',  # before status line
    'FunctionError': '¿',    # when computation fails due to exception
    'HistogramChar': '*',
    'ColumnStats': False,  # whether to include mean/median/etc on 'C'olumn sheet
    'EditPadChar': '_',
    'Unprintable': '.',

    # color scheme
    'c_default': 'normal',
    'c_Header': 'bold',
    'c_CurHdr': 'reverse',
    'c_CurRow': 'reverse',
    'c_CurCol': 'bold',
    'c_KeyCols': 'brown',
    'c_StatusLine': 'bold',
    'c_SelectedRow': 'green',
    'c_ColumnSep': 'blue',
    'c_EditCell': 'normal',
}

class attrdict(object):
    def __init__(self, d):
        self.__dict__ = d

options = attrdict(default_options)
