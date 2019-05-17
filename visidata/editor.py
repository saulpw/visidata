import os
import signal
import subprocess
import tempfile
import curses

import visidata


class SuspendCurses:
    'Context Manager to temporarily leave curses mode'
    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.refresh()
        curses.doupdate()


def launchEditor(*args):
    editor = os.environ.get('EDITOR') or fail('$EDITOR not set')
    args = [editor] + list(args)
    with SuspendCurses():
        return subprocess.call(args)


def launchExternalEditor(v, linenum=0):
    import tempfile
    with tempfile.NamedTemporaryFile() as temp:
        with open(temp.name, 'w') as fp:
            fp.write(v)
        return launchExternalEditorPath(visidata.Path(temp.name))


def launchExternalEditorPath(path, linenum=0):
        fn = path.resolve()
        if linenum:
            launchEditor(fn, '+%s' % linenum)
        else:
            launchEditor(fn)

        with open(fn, 'r') as fp:
            try:
                r = fp.read()
                if r[:-1] == '\n':  # trim inevitable trailing newline
                    r = r[:-1]
                return r
            except Exception as e:
                visidata.exceptionCaught(e)
                return ''

        launchExternalEditor(visidata.Path(temp.name))


def suspend():
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)


visidata.globalCommand('^Z', 'suspend', 'suspend()')
