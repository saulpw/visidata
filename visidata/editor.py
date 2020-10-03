import os
import signal
import subprocess
import tempfile
import curses

import visidata


class SuspendCurses:
    'Context manager to leave windowed mode on enter and restore it on exit.'
    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.refresh()
        curses.doupdate()


@visidata.VisiData.global_api
def launchEditor(vd, *args):
    'Launch $EDITOR with *args* as arguments.'
    editor = os.environ.get('EDITOR') or vd.fail('$EDITOR not set')
    args = [editor] + list(args)
    with SuspendCurses():
        return subprocess.call(args)


@visidata.VisiData.global_api
def launchExternalEditor(vd, v, linenum=0):
    'Launch $EDITOR to edit string *v* starting on line *linenum*.'
    import tempfile
    with tempfile.NamedTemporaryFile() as temp:
        with open(temp.name, 'w') as fp:
            fp.write(v)
        return launchExternalEditorPath(visidata.Path(temp.name), linenum)


def launchExternalEditorPath(path, linenum=0):
        'Launch $EDITOR to edit *path* starting on line *linenum*.'
        if linenum:
            launchEditor(path, '+%s' % linenum)
        else:
            launchEditor(path)

        with open(path, 'r') as fp:
            try:
                return fp.read().rstrip('\n')  # trim inevitable trailing newlines
            except Exception as e:
                visidata.vd.exceptionCaught(e)
                return ''


def suspend():
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)


visidata.globalCommand('^Z', 'suspend', 'suspend()', 'suspend VisiData process')
