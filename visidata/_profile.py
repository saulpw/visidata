import os.path
import functools
import cProfile
import threading
import collections

from visidata import vd, option, options, status, globalCommand, Sheet, EscapeException
from visidata import elapsed_s, ColumnAttr, Column, ThreadsSheet, ENTER

option('profile', '', 'filename to save binary profiling data')

globalCommand('^_', 'toggle-profile', 'toggleProfiling(threading.current_thread())')

ThreadsSheet.addCommand(ENTER, 'profile-row', 'vd.push(ProfileSheet(cursorRow.name+"_profile", source=cursorRow.profile.getstats()))')

min_thread_time_s = 0.10 # only keep threads that take longer than this number of seconds

def open_pyprof(p):
    return ProfileSheet(p.name, p.open_bytes())


def toggleProfiling(t):
    if not t.profile:
        t.profile = cProfile.Profile()
        t.profile.enable()
        if not options.profile:
            options.set('profile', 'vdprofile')
    else:
        t.profile.disable()
        t.profile = None
        options.set('profile', '')
    status('profiling ' + ('ON' if t.profile else 'OFF'))


@functools.wraps(vd().toplevelTryFunc)
def threadProfileCode(func, *args, **kwargs):
    'Toplevel thread profile wrapper.'
    with ThreadProfiler(threading.current_thread()) as prof:
        try:
            prof.thread.status = threadProfileCode.__wrapped__(func, *args, **kwargs)
        except EscapeException as e:
            prof.thread.status = e


class ThreadProfiler:
    numProfiles = 0

    def __init__(self, thread):
        self.thread = thread
        if options.profile:
            self.thread.profile = cProfile.Profile()
        else:
            self.thread.profile = None
        ThreadProfiler.numProfiles += 1
        self.profileNumber = ThreadProfiler.numProfiles

    def __enter__(self):
        if self.thread.profile:
            self.thread.profile.enable()
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if self.thread.profile:
            self.thread.profile.disable()
            self.thread.profile.dump_stats(options.profile + str(self.profileNumber))

        if exc_val:
            self.thread.exception = exc_val
        else:
            # remove very-short-lived async actions
            if elapsed_s(self.thread) < min_thread_time_s:
                vd().threads.remove(self.thread)

class ProfileSheet(Sheet):
    columns = [
        Column('funcname', getter=lambda col,row: codestr(row.code)),
        Column('filename', getter=lambda col,row: os.path.split(row.code.co_filename)[-1] if not isinstance(row.code, str) else ''),
        Column('linenum', type=int, getter=lambda col,row: row.code.co_firstlineno if not isinstance(row.code, str) else None),

        Column('inlinetime_us', type=int, getter=lambda col,row: row.inlinetime*1000000),
        Column('totaltime_us', type=int, getter=lambda col,row: row.totaltime*1000000),
        ColumnAttr('callcount', type=int),
        Column('avg_inline_us', type=int, getter=lambda col,row: row.inlinetime*1000000/row.callcount),
        Column('avg_total_us', type=int, getter=lambda col,row: row.totaltime*1000000/row.callcount),
        ColumnAttr('reccallcount', type=int),
        ColumnAttr('calls'),
        Column('callers', getter=lambda col,row: col.sheet.callers[row.code]),
    ]

    nKeys=3

    def reload(self):
        self.rows = self.source
        self.orderBy(self.column('inlinetime_us'), reverse=True)
        self.callers = collections.defaultdict(list)  # [row.code] -> list(code)

        for r in self.rows:
            calls = getattr(r, 'calls', None)
            if calls:
                for callee in calls:
                    self.callers[callee.code].append(r)


def codestr(code):
    if isinstance(code, str):
        return code
    return code.co_name


ProfileSheet.addCommand('z^S', 'save-profile', 'profile.dump_stats(input("save profile to: ", value=name+".prof"))')
ProfileSheet.addCommand(ENTER, 'dive-row', 'vd.push(ProfileSheet(codestr(cursorRow.code)+"_calls", source=cursorRow.calls or fail("no calls")))')
ProfileSheet.addCommand('z'+ENTER, 'dive-cell', 'vd.push(ProfileSheet(codestr(cursorRow.code)+"_"+cursorCol.name, source=cursorValue or fail("no callers")))')
ProfileSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow.code.co_filename, "+%s" % cursorRow.code.co_firstlineno)')

vd.toplevelTryFunc = threadProfileCode
