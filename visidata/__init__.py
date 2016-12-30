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

option('fn_usercmds', '/home/saul/.vd-usercmds.tsv', 'user commands file to autoload on startup')

def load_user_commands():
    usercmds = options.fn_usercmds

    try:
        vd().user_commands = open_tsv(Path(usercmds), headerlines=0).columns
        vd().status(usercmds + str(len(vd().user_commands)))

    except OSError:
        pass  # vd().status(str(e))
    except Exception:
        vd().exceptionCaught()


def run(sheetlist=[]):
    'main entry point to invoke curses mode'

    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    ret = wrapper(curses_main, sheetlist)
    if ret:
        print(ret)


def curses_main(_scr, sheetlist=[]):
    load_user_commands()
    for vs in sheetlist:
        vd().push(vs)  # first push does a reload
    return vd().run(_scr)
