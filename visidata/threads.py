import ctypes
import time
import os.path
import functools
import cProfile
import threading
import collections

from visidata import VisiData, vd, options, globalCommand, Sheet, EscapeException
from visidata import ColumnAttr, Column
from visidata import *


vd.option('profile', False, 'enable profiling on threads')
vd.option('min_memory_mb', 0, 'minimum memory to continue loading and async processing')

vd.option('color_working', 'green', 'color of system running smoothly')

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


class _Progress:
    def __init__(self, iterable=None, gerund="", total=None, sheet=None):
        self.iterable = iterable
        if total is None:
            if iterable is not None:
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
            self.sheet.progresses.insert(0, self)
        return self

    def addProgress(self, n):
        'Increase the progress count by *n*.'
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

@VisiData.global_api
def Progress(vd, iterable=None, gerund="", total=None, sheet=None):
    '''Maintain progress count as either an iterable wrapper, or a context manager.

        - *iterable*: wrapped iterable if used as an iterator.
        - *gerund*: status text shown while this Progress is active.
        - *total*: total count expected.
        - *sheet*: specific sheet to associate this progress with.  Default is sheet from current thread.
        '''
    return _Progress(iterable=iterable, gerund=gerund, total=total, sheet=sheet)


@VisiData.api
def cancelThread(vd, *threads, exception=EscapeException):
    'Raise *exception* in one or more *threads*.'
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
        self.rows = self.source

    def openRow(self, row):
        'push profile sheet for this action'
        if row.profile:
            return ProfileSheet(row.name, "profile", source=row.profile)
        vd.warning("no profile")


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
        try:
            freestats = subprocess.run('free --total --mega'.split(), check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip().splitlines()
        except FileNotFoundError as e:
            if options.debug:
                vd.exceptionCaught(e)
            options.min_memory_mb = 0
            vd.warning('disabling min_memory_mb: "free" not installed')
            return '', attr
        tot_m, used_m, free_m = map(int, freestats[-1].split()[1:])
        ret = '[%dMB] ' % free_m + ret
        if free_m < min_mem:
            attr = 'color_warning'
            vd.warning('%dMB free < %dMB minimum, stopping threads' % (free_m, min_mem))
            vd.cancelThread(*vd.unfinishedThreads)
            curses.flash()
    return ret, attr


# for progress bar
BaseSheet.init('progresses', list)  # list of Progress objects

@BaseSheet.property
def progressMade(self):
    return sum(prog.made for prog in self.progresses if prog.total)

@BaseSheet.property
def progressTotal(self):
    return sum(prog.total for prog in self.progresses)


@BaseSheet.property
def progressPct(sheet):
    'Percent complete string as indicated by async actions.'
    if sheet.progresses and sheet.progressTotal > 0:
        return '%2d%%' % int(sheet.progressMade*100//sheet.progressTotal)
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

@VisiData.api
def execAsync(self, func, *args, sheet=None, **kwargs):
    'Execute ``func(*args, **kwargs)`` in a separate thread.'

    thread = threading.Thread(target=_toplevelTryFunc, daemon=True, args=(func,)+args, kwargs=kwargs)
    self.threads.append(_annotate_thread(thread))

    if sheet is None:
        sheet = self.activeSheet

    if sheet is not None:
        sheet.currentThreads.append(thread)

    thread.sheet = sheet
    thread.start()

    return thread

def _toplevelTryFunc(func, *args, status=vd.status, **kwargs):
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
        vd.exceptionCaught(e)

    if t.sheet:
        t.sheet.currentThreads.remove(t)

def asyncsingle(func):
    '''Function decorator like `@asyncthread` but as a singleton.  When called, `func(...)` spawns a new thread, and cancels any previous thread still running *func*.
    ``vd.sync()`` does not wait for unfinished asyncsingle threads.
    '''
    @functools.wraps(func)
    def _execAsync(*args, **kwargs):
        def _func(*args, **kwargs):
            func(*args, **kwargs)
            _execAsync.searchThread = None
            # end of thread

        # cancel previous thread if running
        if _execAsync.searchThread:
            vd.cancelThread(_execAsync.searchThread)

        _func.__name__ = func.__name__ # otherwise, the the thread's name is '_func'

        _execAsync.searchThread = vd.execAsync(_func, *args, **kwargs)
        _execAsync.searchThread.noblock = True
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
    'Wait for one or more *joiningThreads* to finish. If no *joiningThreads* specified, wait for all but current thread and interface thread to finish.'
    joiningThreads = set(joiningThreads)
    while True:
        deads = set()  # dead threads
        threads = joiningThreads or set(self.unfinishedThreads)
        threads -= set([threading.current_thread(), getattr(vd, 'drawThread', None)])
        threads -= deads
        for t in threads:
            try:
                if not t.is_alive() or t not in threading.enumerate() or getattr(t, 'noblock', False) is True:
                    deads.add(t)
                else:
                    t.join(timeout=1)
            except RuntimeError as e:  # maybe thread hasn't started yet or has already joined
                vd.exceptionCaught(e)
                pass

        if len(threads - deads) == 0:
            break


min_thread_time_s = 0.10 # only keep threads that take longer than this number of seconds

@VisiData.api
def open_pyprof(vd, p):
    import pstats
    return ProfileStatsSheet(p.name, source=pstats.Stats(p.given).stats)


@VisiData.api
def toggleProfiling(vd):
    t = threading.current_thread()
    if not t.profile:
        t.profile = cProfile.Profile()
        t.profile.enable()
        if not vd.options.profile:
            vd.options.set('profile', True)
    else:
        t.profile.disable()
        vd.options.set('profile', False)
    vd.status('profiling ' + ('ON' if vd.options.profile else 'OFF'))


class ThreadProfiler:
    def __init__(self, thread):
        self.thread = thread
        self.thread.profile = cProfile.Profile()

    def __enter__(self):
        if vd.options.profile:
            self.thread.profile.enable()
        return self

    def __exit__(self, exc_type, exc_val, tb):
        self.thread.profile.disable()

        if exc_val:
            self.thread.exception = exc_val
        else:
            # remove very-short-lived async actions
            if elapsed_s(self.thread) < min_thread_time_s:
                vd.threads.remove(self.thread)


class ProfileSheet(Sheet):
    rowtype = 'callsites' # rowdef: profiler_entry
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
        if isinstance(self.source, cProfile.Profile):
            self.rows = self.source.getstats()
        else:
            self.rows = self.source

        self.orderBy(None, self.column('inlinetime_us'), reverse=True)
        self.callers = collections.defaultdict(list)  # [row.code] -> list(code)

        for r in self.rows:
            calls = getattr(r, 'calls', None)
            if calls:
                for callee in calls:
                    self.callers[callee.code].append(r)

    def openRow(self, row):
        'open ProfileSheet for calls referenced in current row'
        if row.calls:
            return ProfileSheet(codestr(row.code)+"_calls", source=row.calls)
        vd.warning("no calls")

    def openCell(self, col, row):
        'open ProfileSheet for caller referenced in current cell'
        val = col.getValue(row)
        if val:
            return ProfileSheet(codestr(row.code)+"_"+col.name, source=val)
        vd.warning("no callers")


class ProfileStatsSheet(Sheet):
    rowtype = 'functions' # rowdef: list from pstats.Stats.stats
    columns = [
        ItemColumn('pathname', 0),
        ItemColumn('line', 1, type=int),
        ItemColumn('func', 2),
        ItemColumn('ncalls', 3, type=int),
        ItemColumn('primitive_calls', 4, type=int, width=0),
        ItemColumn('tottime', 5, type=float),
        ItemColumn('cumtime', 6, type=float),
        ItemColumn('callers', 7),
    ]
    def reload(self):
        self.rows = list((k+v) for k,v in self.source.items())

    def openRow(self, row):
        return ProfileStatsSheet('', source=row[7])

def codestr(code):
    if isinstance(code, str):
        return code
    return code.co_name


ThreadsSheet.addCommand('^C', 'cancel-thread', 'cancelThread(cursorRow)', 'abort thread at current row')
ThreadsSheet.addCommand('g^C', 'cancel-all', 'cancelThread(*sheet.rows)', 'abort all threads on this threads sheet')
ThreadsSheet.addCommand(None, 'add-row', 'fail("cannot add new rows on Threads Sheet")', 'invalid command')

ProfileSheet.addCommand('z^S', 'save-profile', 'source.dump_stats(input("save profile to: ", value=name+".prof"))', 'save profile')
ProfileSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow.code.co_filename, "+%s" % cursorRow.code.co_firstlineno)', 'open current file at referenced row in external $EDITOR')
ProfileStatsSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow[0], "+%s" % cursorRow[1])', 'open current file at referenced row in external $EDITOR')

BaseSheet.addCommand('^_', 'toggle-profile', 'toggleProfiling()', 'Enable or disable profiling on main VisiData process')

BaseSheet.addCommand('^C', 'cancel-sheet', 'cancelThread(*sheet.currentThreads or fail("no active threads on this sheet"))', 'abort all threads on current sheet')
BaseSheet.addCommand('g^C', 'cancel-all', 'liveThreads=list(t for vs in vd.sheets for t in vs.currentThreads); cancelThread(*liveThreads); status("canceled %s threads" % len(liveThreads))', 'abort all spawned threads')


BaseSheet.addCommand('^T', 'threads-all', 'vd.push(ThreadsSheet("threads", source=vd.threads))', 'open Threads for all sheets')
BaseSheet.addCommand('z^T', 'threads-sheet', 'vd.push(ThreadsSheet("threads", source=sheet.currentThreads))', 'open Threads for this sheet')

vd.addGlobals({
    'ThreadsSheet': ThreadsSheet,
    'Progress': Progress,
    'asynccache': asynccache,
    'asyncsingle': asyncsingle,
})
