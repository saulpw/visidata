import ctypes
import threading
import pstats
import cProfile

from visidata import *

option('profile_tasks', True, 'profile async tasks')
option('min_task_time', 0.10, 'only keep tasks that take longer than this number of seconds')

command('^C', 'if sheet.currentTask: ctypeAsyncRaise(sheet.currentTask.thread, EscapeException)', 'cancel task on the current sheet')
command('^T', 'vd.push(vd.taskMgr)', 'push task history sheet')
command('^U', 'toggleProfiling(vd)', 'turn profiling on for main process')

vd().profile = None
def toggleProfiling(vd):
    if not vd.profile:
        vd.profile = cProfile.Profile()
        vd.profile.enable()
    else:
        vd.profile.disable()
        vd.push(TextSheet("main_profile", getProfileResults(vd.profile)))
        vd.profile = None


# define @async for potentially long-running functions
#   when function is called, instead launches a thread
#   ENTER on that row pushes a profile of the thread

class Task:
    'Prepare function and its parameters for asynchronous processing.'
    def __init__(self, name):
        self.name = name
        self.startTime = time.process_time()
        self.endTime = None
        self.status = ''
        self.thread = None
        self.profileResults = None

    def start(self, func, *args, **kwargs):
        'Start parallel thread.'
        self.thread = threading.Thread(target=func, daemon=True, args=args, kwargs=kwargs)
        self.thread.start()

    @property
    def elapsed_s(self):
        'Return elapsed time.'
        return (self.endTime or time.process_time())-self.startTime

def sync():
    while len(vd().taskMgr.unfinishedTasks) > 0:
        vd().taskMgr.checkForUnfinishedTasks()

def execAsync(func, *args, **kwargs):
    'Manage execution of asynchronous thread, checking for redundancy.'
    if threading.current_thread().daemon:
        # Don't spawn a new thread from a subthread.
        return func(*args, **kwargs)

    currentSheet = vd().sheets[0]
    if currentSheet.currentTask:
        error('A task is already in progress on this sheet')
    t = Task(' '.join([func.__name__] + [str(x) for x in args[:1]]))
    currentSheet.currentTask = t
    t.sheet = currentSheet
    if bool(options.profile_tasks):
        t.start(threadProfileCode, t, func, *args, **kwargs)
    else:
        t.start(toplevelTryFunc, t, func, *args, **kwargs)
    vd().taskMgr.rows.append(t)
    return t

def toplevelTryFunc(task, func, *args, **kwargs):
    'Modify status-bar content on user-abort/exceptions, for use by @async.'
    ret = None
    try:
        ret = func(*args, **kwargs)
    except EscapeException as e:  # user aborted
        task.status += 'aborted by user;'
        status('%s aborted' % task.name)
    except Exception as e:
        task.status += status('%s: %s;' % (type(e).__name__, ' '.join(str(x) for x in e.args)))
        exceptionCaught()

    task.sheet.currentTask = None
    return ret

def threadProfileCode(task, func, *args, **kwargs):
    'Wrap profiling functionality for use by @async.'
    pr = cProfile.Profile()
    pr.enable()
    ret = toplevelTryFunc(task, func, *args, **kwargs)
    pr.disable()
    task.profileResults = getProfileResults(pr)
    return ret

def getProfileResults(pr):
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.strip_dirs()
    ps.print_stats()
    return s.getvalue()

def ctypeAsyncRaise(threadObj, exception):
    'Raise exception for threads running asynchronously.'


    def dictFind(D, value):
        'Return first key in dict `D` corresponding to `value`.'
        for k, v in D.items():
            if v is value:
                return k

    # Following `ctypes call follows https://gist.github.com/liuw/2407154.
    thread = dictFind(threading._active, threadObj)
    if thread:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread), ctypes.py_object(exception))
        status('canceling %s' % threadObj.name)
    else:
        status('no thread to cancel')


# each row is a Task object
class TaskManager(Sheet):
    'Sheet displaying "Task" objects: asynchronous threads.'
    def __init__(self):
        super().__init__('task_history')
        self.command('^C', 'ctypeAsyncRaise(cursorRow.thread, EscapeException)', 'cancel this action')
        self.command(ENTER, 'vd.push(TextSheet(cursorRow.name+"_profile", cursorRow.profileResults))', 'push profile sheet for this action')

        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('elapsed_s', type=float),
            ColumnAttr('status'),
        ]

    @property
    def unfinishedTasks(self):
        'Return list of tasks for which `endTime` has not been reached.'
        return [task for task in self.rows if not task.endTime]

    def checkForUnfinishedTasks(self):
        'Prune old threads that were not started or terminated.'
        for task in self.unfinishedTasks:
            if not task.thread.is_alive():
                task.endTime = time.process_time()
                task.status += 'ended'
                if task.elapsed_s*1000 < float(options.min_task_time):
                    self.rows.remove(task)


vd().taskMgr = TaskManager()

vd().addHook('predraw', vd().taskMgr.checkForUnfinishedTasks)
vd().execAsync = execAsync

