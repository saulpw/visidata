import ctypes
import time
import os.path
import functools
import cProfile
import threading
import collections
import subprocess
import curses

from visidata import VisiData, vd, options, globalCommand, Sheet, EscapeException
from visidata import ColumnAttr, Column, BaseSheet, ItemColumn


vd.option('profile', False, 'enable profiling on threads')
vd.option('min_memory_mb', 0, 'minimum memory to continue loading and async processing')

vd.theme_option('color_working', '118 5', 'color of system running smoothly')

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
        if t.ident is not None:
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
    threads = vd.unfinishedThreads
    if not threads:
        return ''

    min_mem = vd.options.min_memory_mb
    if not min_mem:
        return ''

    try:
        freestats = subprocess.run('free --total --mega'.split(), check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip().splitlines()
    except FileNotFoundError as e:
        if vd.options.debug:
            vd.exceptionCaught(e)
        vd.options.min_memory_mb = 0
        vd.warning('disabling min_memory_mb: "free" not installed')
        return ''
    tot_m, used_m, free_m = map(int, freestats[-1].split()[1:])
    ret = f'  [{free_m}MB] '
    if free_m < min_mem:
        attr = '[:warning]'
        vd.warning(f'{free_m}MB free < {min_mem}MB minimum, stopping threads')
        vd.cancelThread(*vd.unfinishedThreads)
        curses.flash()
    else:
        attr = '[:working]'
    return attr + ret + '[/]'


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
vd.threads = [_annotate_thread(threading.current_thread(), 0)]

@VisiData.api
def execSync(vd, func, *args, sheet=None, **kwargs):
    'Execute ``func(*args, **kwargs)`` in this thread (synchronously). A drop-in substitute for vd.execAsync.'
    vd.callNoExceptions(func, *args, **kwargs)
    t = threading.current_thread()
    t.sheet = sheet or vd.activeSheet
    return t

@VisiData.api
def execAsync(vd, func, *args, **kwargs):
    '''Execute ``func(*args, **kwargs)`` in a separate thread.  `sheet` is a
    special kwarg to indicate which sheet the thread should be associated with;
    by default, uses vd.activeSheet.  If `sheet` explicitly given as None, the thread
    will be ignored by vd.sync and thread status indicators.
    '''

    if 'sheet' not in kwargs:
        sheet = vd.activeSheet
    else:
        sheet = kwargs.pop('sheet')

    if sheet is not None and (sheet.lastCommandThreads and threading.current_thread() not in sheet.lastCommandThreads):
        vd.fail(f'still running **{sheet.lastCommandThreads[-1].name}** from previous command')

    # the current thread's activeCommand
    cmd = vd.activeCommand
    # the newly started thread is assigned the same activeCommand
    def _with_active_cmd(func, *args, **kwargs):
        if cmd: vd.activeCommand = cmd
        _toplevelTryFunc(func, *args, **kwargs)
        if cmd: vd.activeCommand = None
    thread = threading.Thread(target=_with_active_cmd, daemon=True, args=(func,)+args, kwargs=kwargs)
    vd.threads.append(_annotate_thread(thread))

    if sheet is not None:
        sheet.currentThreads.append(thread)

    thread.sheet = sheet
    thread.start()

    return thread

def _toplevelTryFunc(func, *args, **kwargs):
  with ThreadProfiler(threading.current_thread()) as prof:
    t = threading.current_thread()
    t.name = func.__name__
    try:
        t.status = func(*args, **kwargs)
    except EscapeException as e:  # user aborted
        t.status = 'aborted by user'
        vd.warning(f'{t.name} aborted')
    except Exception as e:
        t.exception = e
        t.status = 'exception'
        vd.exceptionCaught(e)

    if t.sheet:
        t.sheet.currentThreads.remove(t)

def asyncignore(func):
    'Decorator like `@asyncthread` but without attaching to a sheet, so no sheet.threadStatus will show it.'
    @functools.wraps(func)
    def _execAsync(*args, **kwargs):
        @functools.wraps(func)
        def _func(*args, **kwargs):
            func(*args, **kwargs)

        return vd.execAsync(_func, *args, **kwargs, sheet=None)

    return _execAsync

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
    return [t for t in self.threads if getattr(t, 'endTime', None) is None and getattr(t, 'sheet', None) is not None]

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
        threads -= set([threading.current_thread(), getattr(vd, 'drawThread', None), getattr(vd, 'outputProgressThread', None)])
        threads -= deads
        threads -= set([None])
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
    return ProfileStatsSheet(p.base_stem, source=pstats.Stats(p.given).stats)


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
            else:
                if self.thread.sheet:
                    if vd.options.profile:
                        vd.status(f'[:bold]{self.thread.sheet.name[:32]}.{self.thread.name}[/] finished in {elapsed_s(self.thread):.1f}s')
                if vd.options.profile:
                    self.thread.profile.dump_stats(f'{self.thread.name}.pyprof')


class ProfileSheet(Sheet):
    rowtype = 'callsites' # rowdef: profiler_entry
    guide = '''
        # Profile Sheet
        - `z Ctrl+S` to save as pyprof file
        - `Ctrl+O` to open current function in $EDITOR
        - `Enter` to open list of calls from current function
    '''
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
    'asyncignore': asyncignore,
})

vd.addMenuItems('''
    System > Threads sheet > threads-all
    System > Toggle profiling > toggle-profile
''')
