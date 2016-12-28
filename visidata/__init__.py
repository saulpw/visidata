#
# VisiData: a curses interface for exploring and arranging tabular data
#
# Copyright (C) 2017 Saul Pwanson
#

__version__ = '0.40'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__license__ = 'GPLv3'
__status__ = 'Development'

def vdglobals():
    return globals()

from .core import *
from .types import *
from .columns import *
from .sheets import *
from .loaders import *

# display/color scheme
theme('SheetNameFmt', '%s| ', 'status line prefix')
theme('ch_VisibleNone', '',  'visible contents of a cell whose value was None')
theme('ch_FunctionError', '¿', 'when computation fails due to exception')
theme('ch_Histogram', '*')
theme('ch_ColumnFiller', ' ', 'pad chars after column value')
theme('ch_LeftMore', '<')
theme('ch_RightMore', '>')
theme('ch_ColumnSep', '|', 'chars between columns')
theme('ch_Ellipsis', '…')
theme('ch_StatusSep', ' | ')
theme('ch_KeySep', '/')
theme('ch_EditPadChar', '_')
theme('ch_Newline', '\\n', 'displayable newline')
theme('ch_Unprintable', '.')
theme('ch_WrongType', '~')
theme('ch_Error', '!')

theme('c_default', 'normal')
theme('c_Header', 'bold')
theme('c_CurHdr', 'reverse')
theme('c_CurRow', 'reverse')
theme('c_CurCol', 'bold')
theme('c_KeyCols', 'brown')
theme('c_StatusLine', 'bold')
theme('c_SelectedRow', 'green')
theme('c_ColumnSep', 'blue')
theme('c_EditCell', 'normal')
theme('c_WrongType', 'magenta')
theme('c_Error', 'red')


def run(sheetlist=None):
    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    ret = wrapper(curses_main, sheetlist)
    if ret:
        print(ret)


def curses_main(_scr, sheetlist=None):
    try:
        if sheetlist:
            for vs in sheetlist:
                vd().push(vs)  # first push does a reload
        return vd().run(_scr)
    except Exception as e:
        if options.debug:
            raise
        return '%s: %s' % (type(e).__name__, str(e))
