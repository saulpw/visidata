from visidata import *


@VisiData.api
def new_top(vd, p):
    return vd.processes


class CPUStatsSheet(Sheet):
    rowtype='CPUs'  # rowdef = (count, perfect, times, freq) from psutil (see below)
    columns = [
        ColumnItem('cpu', 0, type=int, keycol=0),
        ColumnItem('cpu_pct', 1, type=float)
    ]
    def iterload(self):
        psutil = vd.importExternal('psutil')

        for i, k in enumerate(psutil.cpu_times()._fields):
            self.addColumn(SubColumnItem(2, ColumnItem(k+'_s', i, type=float, sheet=self)))

        for i, k in enumerate(psutil.cpu_freq()._fields):
            self.addColumn(SubColumnItem(3, ColumnItem(k+'_MHz', i, type=float, sheet=self)))

        for r in zip(range(psutil.cpu_count()),
                        psutil.cpu_percent(percpu=True),
                        psutil.cpu_times(percpu=True),
                        psutil.cpu_freq(percpu=True)):
            yield r



class MemStatsSheet(Sheet):
    rowtype = ''  # rowdef: (name, value)
    columns = [
        AttrColumn('t', type=date, fmtstr='%H:%M:%S'),
        AttrColumn('meminfo'),
        AttrColumn('virtmem'),
        AttrColumn('swapmem'),
    ]
    nKeys = 1

    def iterload(self):
        psutil = vd.importExternal('psutil')
        import time

        proc = psutil.Process()

        while True:
            yield AttrDict(t=time.time(),
                         virtmem=psutil.virtual_memory(),
                         swapmem=psutil.swap_memory(),
                         meminfo=proc.memory_info(),
                        )

            if self.nRows == 1:  # first time through
                for n in 'meminfo virtmem swapmem'.split():
                    c = self.column(n)
                    if not c.hidden:
                        c.expand([self.rows[0]])

            time.sleep(1)


class UsefulProcessesSheet(Sheet):
    columns = [
        Column('pid', type=int, getter=lambda c,r: r[0].pid),
        Column('name', getter=lambda c,r: r[0].name()),
        Column('status', getter=lambda c,r: r[0].status()),
        Column('cmdline', getter=lambda c,r: ' '.join(r[0].cmdline())),
        Column('user', getter=lambda c,r: r[0].username()),
        Column('real_uid', type=int, width=0, getter=lambda c,r: r[0].uids()[0]),
        Column('effective_uid', type=int, width=0, getter=lambda c,r: r[0].uids()[1]),
        Column('mem_uss', type=int, getter=lambda c,r: r[1].mem_uss),
        Column('user_time_s', type=float, getter=lambda c,r: r[0].cpu_times()[0]),
        Column('system_time_s', type=float, getter=lambda c,r: r[0].cpu_times()[1]),
    ]
    def iterload(self):
        psutil = vd.importExternal('psutil')
        for pr in psutil.process_iter():
            yield (pr, pr.memory_full_info())


class ProcessesSheet(Sheet):
    columns = [
        Column('pid', type=int, getter=lambda c,r: r.pid),
        Column('name', getter=lambda c,r: r.name()),
        Column('status', getter=lambda c,r: r.status()),
        Column('parent_pid', type=int, getter=lambda c,r: r.ppid()),
        Column('exe', getter=lambda c,r: r.exe()),
        Column('cmdline', getter=lambda c,r: ' '.join(r.cmdline())),
        Column('cwd', getter=lambda c,r: r.cwd()),
        Column('user', getter=lambda c,r: r.username()),

        Column('real_uid', type=int, width=0, getter=lambda c,r: r.uids()[0]),
        Column('effective_uid', type=int, width=0, getter=lambda c,r: r.uids()[1]),
        Column('saved_uid', type=int, width=0, getter=lambda c,r: r.uids()[2]),

        Column('real_gid', type=int, width=0, getter=lambda c,r: r.gids()[0]),
        Column('effective_gid', type=int, width=0, getter=lambda c,r: r.gids()[1]),
        Column('saved_gid', type=int, width=0, getter=lambda c,r: r.gids()[2]),

        Column('create_time', type=date, getter=lambda c,r: r.create_time()),
        Column('cpu_num', type=int, getter=lambda c,r: r.cpu_num()),
        Column('cpu_percent', type=float, getter=lambda c,r: r.cpu_percent()),

        Column('tty', getter=lambda c,r: r.terminal()),
        Column('nice', getter=lambda c,r: r.nice()),
        Column('ioclass', getter=lambda c,r: r.ionice()[0]),
        Column('ionice', getter=lambda c,r: r.ionice()[1]),

        Column('user_time_s', type=float, getter=lambda c,r: r.cpu_times()[0]),
        Column('system_time_s', type=float, getter=lambda c,r: r.cpu_times()[1]),
        Column('children_user_time_s', type=float, width=0, getter=lambda c,r: r.cpu_times()[2]),
        Column('children_system_time_s', type=float, width=0, getter=lambda c,r: r.cpu_times()[3]),

        Column('read_ops', type=int, getter=lambda c,r: r.io_counters()[0]),
        Column('write_ops', type=int, getter=lambda c,r: r.io_counters()[1]),
        Column('read_bytes', type=int, getter=lambda c,r: r.io_counters()[2]),
        Column('write_bytes', type=int, getter=lambda c,r: r.io_counters()[3]),

        Column('voluntary_ctx_switches', type=int, getter=lambda c,r: r.num_ctx_switches()[0]),
        Column('involuntary_ctx_switches', type=int, getter=lambda c,r: r.num_ctx_switches()[1]),
        Column('num_fds', type=int, getter=lambda c,r: r.num_fds()),
        Column('num_threads', type=int, getter=lambda c,r: r.num_threads()),
    ]
    nKeys = 2

    def iterload(self):
        psutil = vd.importExternal('psutil')
#        self.columns = []
#        for c in ProcessesSheet.columns:
#            self.addColumn(c)

        for i,k in enumerate(psutil.Process().memory_full_info()._fields):
            self.addColumn(Column('mem_'+k, type=int, getter=lambda c,r,i=i: r.memory_full_info()[i], cache=True))
        # mem_uss is probably the most representative metric for determining how much memory is actually being used by a process. It represents the amount of memory that would be freed if the process was terminated right now.

        yield from psutil.process_iter()
#            try:
#                self.addRow((pr, pr.memory_full_info()))
#            except:
#                self.addRow((pr, None))

class RlimitsSheet(Sheet):
    columns = [
        ColumnItem('rlimit', 0),
        Column('soft', type=int, getter=lambda c,r: c.sheet.soft(r), setter=lambda c,r,v: c.sheet.set_soft(r, v)),
        Column('hard', type=int, getter=lambda c,r: c.sheet.hard(r), setter=lambda c,r,v: c.sheet.set_hard(r, v))
    ]

    def soft(self, r):
        return self.source.rlimit(r[1])[0]
    def hard(self, r):
        return self.source.rlimit(r[1])[1]
    def set_soft(self, r, v):
        self.source.rlimit(r[1], (v, self.hard(r)))
    def set_hard(self, r, v):
        self.source.rlimit(r[1], (self.soft(r), v))

    def iterload(self):
        psutil = vd.importExternal('psutil')
        for r in dir(psutil):
            if r.startswith('RLIMIT'):
                yield (r[7:], getattr(psutil, r))


@VisiData.lazy_property
def cpuStats(vd):
    return CPUStatsSheet('cpu_stats')

@VisiData.lazy_property
def memStats(vd):
    return MemStatsSheet('memory_stats')

@VisiData.lazy_property
def processes(vd):
    return ProcessesSheet('processes')


BaseSheet.addCommand('', 'open-cpustats', 'vd.push(vd.cpuStats)', 'open CPU usage stats' )
BaseSheet.addCommand('', 'open-memstats', 'vd.push(vd.memStats)', 'open memory usage stats')
BaseSheet.addCommand('', 'open-processes', 'vd.push(vd.processes)', 'open system process stats')

@VisiData.api
def chooseSignal(vd):
    import signal
    d = [{'key': attr[3:]} for attr in dir(signal) if attr.startswith('SIG') and not attr.startswith('SIG_')]
    return getattr(signal, 'SIG'+vd.chooseOne(d, type='signal'))

ProcessesSheet.addCommand('d', 'term-process', 'os.kill(cursorRow.pid, signal.SIGTERM)', 'send SIGTERM to process')
ProcessesSheet.addCommand('gd', 'term-selected', 'for r in someSelectedRows: os.kill(r.pid, signal.SIGTERM)', 'send SIGTERM to selected processes')
ProcessesSheet.addCommand('zd', 'kill-process', 'os.kill(cursorRow.pid, signal.SIGKILL)', 'send SIGKILL to process')
ProcessesSheet.addCommand('gzd', 'kill-selected', 'for r in someSelectedRows: os.kill(r.pid, signal.SIGKILL)', 'send SIGKILL to selected processes')

ProcessesSheet.addCommand('^K', 'signal-process', 'os.kill(cursorRow.pid, chooseSignal())', 'send chosen signal to process')
UsefulProcessesSheet.addCommand('^K', 'signal-selected', 'os.kill(cursorRow.pid, chooseSignal())', 'kill(2) send chosen signal to process')
UsefulProcessesSheet.addCommand('', 'open-rlimits', 'vd.push(RlimitsSheet(cursorRow.name() + "_rlimits", cursorRow))', 'push rlimits for this process')

vd.addMenuItem('System', 'Signal', 'current process', 'TERMinate', 'term-process')
vd.addMenuItem('System', 'Signal', 'current process', 'KILL', 'kill-process')
vd.addMenuItem('System', 'Signal', 'current process', 'choose signal', 'signal-process')
vd.addMenuItem('System', 'Signal', 'selected processes', 'TERMinate', 'term-selected')
vd.addMenuItem('System', 'Signal', 'selected processes', 'KILL', 'kill-selected')
vd.addMenuItem('System', 'Signal', 'selected processes', 'choose signal', 'signal-selected')
vd.addMenuItem('System', 'Stats', 'CPU', 'open-cpustats')
vd.addMenuItem('System', 'Stats', 'memory', 'open-memstats')
vd.addMenuItem('System', 'Stats', 'processes', 'open-processes')
vd.addMenuItem('System', 'Stats', 'resource limits', 'open-rlimits')
