import os
import signal
import subprocess
import tempfile
import curses

import visidata

visidata.vd.tstp_signal = None

class SuspendCurses:
    'Context manager to leave windowed mode on enter and restore it on exit.'
    def __enter__(self):
        curses.endwin()
        if visidata.vd.tstp_signal:
            signal.signal(signal.SIGTSTP, visidata.vd.tstp_signal)

    def __exit__(self, exc_type, exc_val, tb):
        curses.reset_prog_mode()
        visidata.vd.scrFull.refresh()
        curses.doupdate()


@visidata.VisiData.api
def launchEditor(vd, *args):
    'Launch $EDITOR with *args* as arguments.'
    editor = os.environ.get('EDITOR') or vd.fail('$EDITOR not set')
    args = editor.split() + list(args)
    with SuspendCurses():
        return subprocess.call(args)


@visidata.VisiData.api
def launchBrowser(vd, *args):
    'Launch $BROWSER with *args* as arguments.'
    browser = os.environ.get('BROWSER') or vd.fail('(no $BROWSER) for %s' % args[0])
    args = [browser] + list(args)
    subprocess.call(args)


@visidata.VisiData.api
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
            visidata.vd.launchEditor(path, '+%s' % linenum)
        else:
            visidata.vd.launchEditor(path)

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
