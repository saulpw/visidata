import os
import sys
import signal
import subprocess
import tempfile
import curses

import visidata

visidata.vd.tstp_signal = None

class SuspendCurses:
    'Context manager to leave windowed mode on enter and restore it on exit.'
    def __enter__(self):
        if visidata.vd.scrFull:
            curses.endwin()
        if visidata.vd.tstp_signal:
            signal.signal(signal.SIGTSTP, visidata.vd.tstp_signal)

    def __exit__(self, exc_type, exc_val, tb):
        if visidata.vd.scrFull:
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
    browser = os.environ.get('BROWSER') or vd.fail('no $BROWSER for %s' % args[0])
    vd.status('opening ' + args[0])
    args = [browser] + list(args)
    subprocess.call(args)


@visidata.VisiData.api
def launchExternalEditor(vd, v, linenum=0, binary=False):
    'Launch $EDITOR to edit bytes *v* starting on line *linenum*.'
    import tempfile
    mode = 'wb' if binary else 'w'
    with tempfile.NamedTemporaryFile() as temp:
        temp.close()  #2118 must close before re-opening on windows
        with open(temp.name, mode) as fp:
            fp.write(v)
        return vd.launchExternalEditorPath(visidata.Path(temp.name), linenum, binary=binary)


@visidata.VisiData.api
def launchExternalEditorPath(vd, path, linenum=0, binary=False):
        'Launch $EDITOR to edit *path* starting on line *linenum*.'
        if linenum:
            visidata.vd.launchEditor(path, '+%s' % linenum)
        else:
            visidata.vd.launchEditor(path)

        mode = 'rb' if binary else 'r'
        with open(path, mode) as fp:
            try:
                data = fp.read()
                if binary:
                    return data
                else:
                    return data.rstrip('\n')  # trim inevitable trailing newlines
            except Exception as e:
                visidata.vd.exceptionCaught(e)
                return ''


@visidata.VisiData.api
def suspend(vd):
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)


def _breakpoint(*args, **kwargs):
    import pdb
    class VisiDataPdb(pdb.Pdb):
        def precmd(self, line):
            r = super().precmd(line)
            if not r:
                SuspendCurses.__exit__(None, None, None, None)
            return r

        def postcmd(self, stop, line):
            if stop:
                SuspendCurses.__enter__(None)
            return super().postcmd(stop, line)

    SuspendCurses.__enter__(None)
    VisiDataPdb(nosigint=True).set_trace()


sys.breakpointhook = _breakpoint


visidata.BaseSheet.addCommand('^Z', 'suspend', 'suspend()', 'suspend VisiData process')
visidata.BaseSheet.addCommand('', 'breakpoint', 'breakpoint()', 'drop into pdb REPL')

visidata.vd.addGlobals(SuspendCurses=SuspendCurses)
