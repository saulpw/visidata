import ctypes
import threading
import pstats
import cProfile

from visidata import *

option('profile_tasks', True, 'profile async tasks')
option('min_task_time', 0.10, 'only keep tasks that take longer than this number of seconds')

command('^C', 'if sheet.currentTask: ctypeAsyncRaise(sheet.currentTask.thread, EscapeException)', 'cancel task on the current sheet')
command('^T', 'vd.push(TasksSheet("task_history"))', 'push task history sheet')


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
    while len(g_TaskMgr.unfinishedTasks) > 0:
        g_TaskMgr.checkForUnfinishedTasks()

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
    g_TaskMgr.tasks.append(t)
    return t

def toplevelTryFunc(task, func, *args, **kwargs):
    'Modify status-bar content on user-abort/exceptions, for use by @async.'
    try:
        ret = func(*args, **kwargs)
        task.sheet.currentTask = None
        return ret
    except EscapeException as e:  # user aborted
        task.sheet.currentTask = None
        task.status += 'aborted by user;'
        status("%s aborted" % task.name)
    except Exception as e:
        task.sheet.currentTask = None
        task.status += status('%s: %s;' % (type(e).__name__, ' '.join(str(x) for x in e.args)))
        exceptionCaught()

def threadProfileCode(task, func, *args, **kwargs):
    'Wrap profiling functionality for use by @async.'
    pr = cProfile.Profile()
    pr.enable()
    ret = toplevelTryFunc(task, func, *args, **kwargs)
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    task.profileResults = s.getvalue()
    return ret


def ctypeAsyncRaise(threadObj, exception):
    'Raise exception for threads running asynchronously.'


    def dictFind(D, value):
        'Return first key in dict `D` corresponding to `value`.'
        for k, v in D.items():
            if v is value:
                return k

        raise ValueError("no such value in dict")

    # Following `ctypes call follows https://gist.github.com/liuw/2407154.
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(dictFind(threading._active, threadObj)),
            ctypes.py_object(exception)
            )
    status('sent exception to %s' % threadObj.name)


class TaskManager:
    def __init__(self):
        self.tasks = []

    @property
    def unfinishedTasks(self):
        'Return list of tasks for which `endTime` has not been reached.'
        return [task for task in self.tasks if not task.endTime]

    def checkForUnfinishedTasks(self):
        'Prune old threads that were not started or terminated.'
        for task in self.unfinishedTasks:
            if not task.thread.is_alive():
                task.endTime = time.process_time()
                task.status += 'ended'
                if task.elapsed_s*1000 < float(options.min_task_time):
                    self.tasks.remove(task)

# each row is a Task object
class TasksSheet(Sheet):
    'Sheet displaying "Task" objects: asynchronous threads.'

    def reload(self):
        'Populate sheet via `reload` function.'
        self.command('^C', 'ctypeAsyncRaise(cursorRow.thread, EscapeException)', 'cancel this action')
        self.command(ENTER, 'vd.push(ProfileSheet(cursorRow))', 'push profile sheet for this action')
        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('elapsed_s', type=float),
            ColumnAttr('status'),
        ]
        self.rows = g_TaskMgr.tasks


def ProfileSheet(task):
    'Populate sheet showing profiling results.'
    return TextSheet(task.name + '_profile', task.profileResults)

g_TaskMgr = TaskManager()

vd().addHook('predraw', g_TaskMgr.checkForUnfinishedTasks)
vd().execAsync = execAsync

