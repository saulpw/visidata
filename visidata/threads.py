import ctypes
import threading
import os.path
import functools
import cProfile
import threading
import collections

from visidata import VisiData, vd, option, options, status, globalCommand, Sheet, EscapeException
from visidata import ColumnAttr, Column, ENTER
from visidata import *

__all__ = ['Progress', 'asynccache', 'async_deepcopy', 'elapsed_s', 'cancelThread', 'ThreadsSheet', 'ProfileSheet', 'codestr', 'asyncsingle']


option('profile', '', 'filename to save binary profiling data')
option('min_memory_mb', 0, 'minimum memory to continue loading and async processing')

theme('color_working', 'green', 'color of system running smoothly')

BaseSheet.init('currentThreads', list)

def asynccache(key=lambda *args, **kwargs: str(args)+str(kwargs)):
    def _decorator(func):
        'Function decorator, so first call to `func()` spawns a separate thread. Calls return the Thread until the wrapped function returns; subsequent calls return the cached return value.'
        d = {}  # per decoration cache
        def _func(k, *args, **kwargs):
            d[k] = func(*args, **kwargs)

        @functools.wraps(func)
        def _execAsync(*args, **kwargs):
            k = key(*args, **kwargs)
            if k not in d:
                d[k] = vd.execAsync(_func, k, *args, **kwargs)
            return d.get(k)
        return _execAsync
    return _decorator


class Progress:
    def __init__(self, iterable=None, gerund="", total=None, sheet=None):
        self.iterable = iterable
        if total is None:
            if iterable:
                self.total = len(iterable)
            else:
                self.total = 0
        else:
            self.total = total
        self.sheet = sheet if sheet else getattr(threading.current_thread(), 'sheet', None)
        self.gerund = gerund
        self.made = 0

    def __enter__(self):
        if self.sheet:
            self.sheet.progresses.append(self)
        return self

    def addProgress(self, n):
        self.made += n
        return True

    def __exit__(self, exc_type, exc_val, tb):
        if self.sheet:
            self.sheet.progresses.remove(self)

    def __iter__(self):
        with self as prog:
            for item in self.iterable:
                yield item
                self.made += 1


@asyncthread
def _async_deepcopy(vs, newlist, oldlist):
    for r in Progress(oldlist, 'copying'):
        newlist.append(deepcopy(r))


def async_deepcopy(vs, rowlist):
    ret = []
    _async_deepcopy(vs, ret, rowlist)
    return ret


@VisiData.global_api
def cancelThread(vd, *threads, exception=EscapeException):
    'Raise exception on another thread.'
    for t in threads:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(t.ident), ctypes.py_object(exception))


# each row is an augmented threading.Thread object
class ThreadsSheet(Sheet):
    rowtype = 'threads'
    precious = False
    columns = [
        ColumnAttr('name'),
        Column('process_time', type=float, getter=lambda col,row: elapsed_s(row)),
        ColumnAttr('profile'),
        ColumnAttr('status'),
        ColumnAttr('exception'),
    ]
    def reload(self):
        self.rows = vd.threads

ThreadsSheet.addCommand('^C', 'cancel-thread', 'cancelThread(cursorRow)')

def elapsed_s(t):
    return (t.endTime or time.process_time())-t.startTime


@VisiData.api
def checkMemoryUsage(vd):
    min_mem = options.min_memory_mb
    threads = vd.unfinishedThreads
    if not threads:
        return None
    ret = ''
    attr = 'color_working'
    if min_mem:
        tot_m, used_m, free_m = map(int, os.popen('free --total --mega').readlines()[-1].split()[1:])
        ret = '[%dMB] ' % free_m + ret
        if free_m < min_mem:
            attr = 'color_warning'
            warning('%dMB free < %dMB minimum, stopping threads' % (free_m, min_mem))
            cancelThread(*vd.unfinishedThreads)
            curses.flash()
    return ret, attr


# for progress bar
BaseSheet.init('progresses', list)  # list of Progress objects

@BaseSheet.property
def progressMade(self):
    return sum(prog.made for prog in self.progresses)

@BaseSheet.property
def progressTotal(self):
    return sum(prog.total for prog in self.progresses)

@BaseSheet.property
def progressPct(self):
    'Percent complete as indicated by async actions.'
    if self.progressTotal != 0:
        return int(self.progressMade*100/self.progressTotal)
    return 0

@BaseSheet.property
def processing(self):
    'String of current activity in gerund form for display.'
    if self.currentThreads:
        return ' '+(self.progresses[0].gerund if self.progresses else 'processing')
    return ''

## threads

def _annotate_thread(t, endTime=None):
    t.startTime = time.process_time()
    t.endTime = endTime  # endTime is None means unfinished.  endTime=0 for main thread
    t.status = ''
    t.profile = None
    t.exception = None
    return t

# all long-running threads, including main and finished
VisiData.init('threads', lambda: [_annotate_thread(threading.current_thread(), 0)])

@VisiData.lazy_property
def threadsSheet(self):
    return ThreadsSheet('threads')

@VisiData.api
def execAsync(self, func, *args, sheet=None, **kwargs):
    'Execute `func(*args, **kwargs)` in a separate thread.'

    thread = threading.Thread(target=_toplevelTryFunc, daemon=True, args=(func,)+args, kwargs=kwargs)
    self.threads.append(_annotate_thread(thread))

    if sheet is None and self.sheets:
        sheet = self.sheets[0]

    if sheet is not None:
        sheet.currentThreads.append(thread)

    thread.sheet = sheet
    thread.start()

    return thread

def _toplevelTryFunc(func, *args, status=status, **kwargs):
  with ThreadProfiler(threading.current_thread()) as prof:
    t = threading.current_thread()
    t.name = func.__name__
    try:
        t.status = func(*args, **kwargs)
    except EscapeException as e:  # user aborted
        t.status = 'aborted by user'
        if status:
            status('%s aborted' % t.name, priority=2)
    except Exception as e:
        t.exception = e
        t.status = 'exception'
        exceptionCaught(e)

    if t.sheet:
        t.sheet.currentThreads.remove(t)

def asyncsingle(func):
    'Decorator for an @asyncthread singleton.  Calls `func(...)` in a separate thread, canceling any previous thread for this function.'
    @functools.wraps(func)
    def _execAsync(*args, **kwargs):
        def _func(*args, **kwargs):
            func(*args, **kwargs)
            _execAsync.searchThread = None
            # end of thread

        # cancel previous thread if running
        if _execAsync.searchThread:
            cancelThread(_execAsync.searchThread)

        _execAsync.searchThread = vd.execAsync(_func, *args, **kwargs)
    _execAsync.searchThread = None
    return _execAsync

@VisiData.property
def unfinishedThreads(self):
    'A list of unfinished threads (those without a recorded `endTime`).'
    return [t for t in self.threads if getattr(t, 'endTime', None) is None]

@VisiData.api
def checkForFinishedThreads(self):
    'Mark terminated threads with endTime.'
    for t in self.unfinishedThreads:
        if not t.is_alive():
            t.endTime = time.process_time()
            if getattr(t, 'status', None) is None:
                t.status = 'ended'

@VisiData.api
def sync(self, *joiningThreads):
    'Wait for joiningThreads to finish. If no joiningThreads specified, wait for all but current thread to finish.'
    joiningThreads = list(joiningThreads) or (set(self.unfinishedThreads)-set([threading.current_thread()]))
    while any(t in self.unfinishedThreads for t in joiningThreads):
        for t in joiningThreads:
            try:
                if not t.is_alive():
                    joiningThreads.remove(t)
                    break
                t.join()
            except RuntimeError:  # maybe thread hasn't started yet or has already joined
                pass


ThreadsSheet.addCommand(ENTER, 'profile-row', 'cursorRow.profile and vd.push(ProfileSheet(cursorRow.name+"_profile", source=cursorRow.profile)) or warning("no profile")')

min_thread_time_s = 0.10 # only keep threads that take longer than this number of seconds

def open_pyprof(p):
    return ProfileSheet(p.name, p.open_bytes())

@VisiData.api
def toggleProfiling(vd, t):
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
                vd.threads.remove(self.thread)

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
        self.rows = self.source.getstats()
        self.orderBy(None, self.column('inlinetime_us'), reverse=True)
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


ProfileSheet.addCommand('z^S', 'save-profile', 'source.dump_stats(input("save profile to: ", value=name+".prof"))')
ProfileSheet.addCommand(ENTER, 'dive-row', 'vd.push(ProfileSheet(codestr(cursorRow.code)+"_calls", source=cursorRow.calls or fail("no calls")))')
ProfileSheet.addCommand('z'+ENTER, 'dive-cell', 'vd.push(ProfileSheet(codestr(cursorRow.code)+"_"+cursorCol.name, source=cursorValue or fail("no callers")))')
ProfileSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow.code.co_filename, "+%s" % cursorRow.code.co_firstlineno)')
globalCommand('^_', 'toggle-profile', 'toggleProfiling(threading.current_thread())')

BaseSheet.addCommand('^C', 'cancel-sheet', 'cancelThread(*sheet.currentThreads or fail("no active threads on this sheet"))')
globalCommand('g^C', 'cancel-all', 'liveThreads=list(t for vs in vd.sheets for t in vs.currentThreads); cancelThread(*liveThreads); status("canceled %s threads" % len(liveThreads))')
globalCommand('^T', 'threads-all', 'vd.push(vd.threadsSheet)')
