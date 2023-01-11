# requires shell tools: ping traceroute
#   these tools aren't inlined as they require root privs

import time
from statistics import mean

import sh

from visidata import VisiData, Sheet, Column
from visidata import *

vd.option('ping_count', 3, 'send this many pings to each host')   # TODO: alias to -c
vd.option('ping_interval', 0.1, 'wait between ping rounds, in seconds')   # TODO: alias to -i


@VisiData.api
def new_ping(vd, p):
    pingsheet = PingSheet(p.given, source=p.given)
    return StatsSheet("traceroute_"+pingsheet.name, source=pingsheet)


class StatsSheet(Sheet):
    rowtype='hosts' # rowdef: PingColumn
    columns = [
        Column('hop', type=int, width=5, getter=lambda col,r: col.sheet.source.sources.index(r.ip)+1),
        Column('hostname', getter=lambda col,r: r.name, width=40),
        Column('ip',  getter=lambda col,r: r.ip, width=17),
        Column('avg_ms', type=float, fmtstr='%.1f', getter=lambda col,r: mean(r.getValues(col.sheet.source.rows))),
        Column('max_ms', type=float, fmtstr='%.1f', getter=lambda col,r: max(r.getValues(col.sheet.source.rows))),
        Column('count',  type=int, getter=lambda col,r: len(list(r.getValues(col.sheet.source.rows)))),
    ]
    def reload(self):
        sheet = self.source
        sheet.reload()

        self.rows = sheet.columns


def PingColumn(name, ip):
    return Column(name, ip=ip, getter=lambda c,r: r.get(c.ip), type=float, fmtstr='%0.1f')


class PingSheet(Sheet):
    rowtype = 'pings'  # rowdef: {'time':time.time(), 'hostname': pingtime}
    def __init__(self, *names, source=None, **kwargs):
        super().__init__(*names, source=source, **kwargs)
        self.sources = [source]

    def ping_response(self, row, ip, data):
        for line in data.splitlines():
            m = re.search(r'from ([0-9\.]+).* time=(.*) ms', line)
            if m:
                row[ip] = m.group(2)
#                assert ip == m.group(1)

    def traceroute_response(self, ip, data):
        for line in data.splitlines():
            m = re.search(r'(\d+)  (\S+) \((\S+)\)  (.*) ms', line)
            if m:
                ttl, hostname, inner_ip, latency_ms = m.groups()
                self.routes[ip][int(ttl)-1] = inner_ip
                if inner_ip == ip:
                    return  # traceroute work is done, let ping do the rest

                if inner_ip not in self.sources:
                    self.sources.insert(-1, inner_ip)
                    self.addColumn(PingColumn(hostname, inner_ip), index=-1)
                    self.send_trace(ip, int(ttl)+1)  # get next hop
                break

    def ping_error(self, ip, data):
        if ip in self.sources:
            self.sources.remove(ip)
            vd.warning("%s removed: %s" % (ip, data))

    def update_traces(self, row, ip):
        rtes = self.routes.get(ip)
        if rtes is None:
            rtes = []
            self.routes[ip] = rtes

        if ip in rtes:
            return

        for i, inner_ip in enumerate(rtes):
            if inner_ip is None:
                self.send_trace(ip, i+1)

        self.send_trace(ip, len(rtes)+1)  # and one more for the road

    def send_trace(self, ip, n):
        while n > len(self.routes[ip]):
            self.routes[ip].append(None)

        sh.traceroute('--sim-queries=1',
                      '--queries=1',
                      '--first=%s' % n,
                      '--max-hops=%s' % n,
                      ip,
                      _bg=True, _bg_exc=False,
                      _out=lambda data,self=self,ip=ip,a=1: self.traceroute_response(ip, data),
                      _err=lambda data,self=self,ip=ip,a=1: self.ping_error(ip, data))

    @asyncthread
    def reload(self):
        self.stop = False
        self.start_time = time.time()
        self.columns = []

        for ip in self.sources:
            self.addColumn(PingColumn(ip, ip))

        self.routes = {}
        self.rows = []
        pings_sent = {}
        ping_count = self.options.ping_count
        with Progress(total=ping_count*len(self.sources), gerund='pinging') as prog:
          while not self.stop:
            r = {'time':time.time()}
            self.addRow(r)

            npings = 0  # this loop
            for ip in self.sources:
                self.update_traces(r, ip)
                pings_sent[ip] = pings_sent.get(ip, 0)+1
                if ping_count and pings_sent[ip] <= ping_count:
                    sh.ping('-c', '1', ip, _bg=True, _bg_exc=False, _timeout=30,
                            _out=lambda data,self=self,r=r,ip=ip: self.ping_response(r,ip,data),
                            _err=lambda data,self=self,ip=ip,a=1: self.ping_error(ip, data))
                    npings += 1
                else:
                    r[ip] = None

            if npings == 0:
                vd.status('no more pings to send')
                break

            time.sleep(self.options.ping_interval)


PingSheet.class_options.null_value = False
