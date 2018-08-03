import struct
import collections
import functools

from visidata import *

def _ord(c):
    return struct.unpack('B', c)[0]

protocols = collections.defaultdict(dict)  # ['ethernet'] = {[6] -> 'IP'}
_flags = collections.defaultdict(dict)  # ['tcp'] = {[4] -> 'FIN'}
oui = {}  # [macprefix (like '01:02:dd:0')] -> 'manufacturer'
services = {}  # [('tcp', 25)] -> 'smtp'


def FlagGetter(flagfield):
    def flags_func(fl):
        return ' '.join([flagname for f, flagname in _flags[flagfield].items() if fl & f])
    return flags_func


def init_pcap():
    if protocols:  # already init'ed
        return

    global dpkt, dnslib
    import dpkt
    import dnslib

    load_consts(protocols['ethernet'], dpkt.ethernet, 'ETH_TYPE_')
    load_consts(protocols['ip'], dpkt.ip, 'IP_PROTO_')
    load_consts(_flags['ip_tos'], dpkt.ip, 'IP_TOS_')
    load_consts(protocols['icmp'], dpkt.icmp, 'ICMP_')
    load_consts(_flags['tcp'], dpkt.tcp, 'TH_')

    try:
        vsoui = open_tsv(Path('wireshark-oui.tsv'))
        vsoui.reload_sync()
        for macslash, shortname, _ in vsoui.rows:
            if macslash.endswith('/36'): prefix = macslash[:13]
            elif macslash.endswith('/28'): prefix = macslash[:13]
            else: prefix = macslash[:13]
            oui[prefix.lower()] = shortname
    except Exception as e:
        pass # exceptionCaught(e)

    try:
        ports_tsv = open_tsv(Path('iana-ports.tsv'))
        ports_tsv.reload_sync()
        for r in ports_tsv.rows:
            services[(r.transport, int(r.port))] = r.service
    except Exception as e:
        pass # exceptionCaught(e)


class Host:
    dns = {}  # [ipstr] -> dnsname
    hosts = {}  # [hostid] -> Host

    @classmethod
    def get(cls, hostid):
        'hostid could be ethermac, ipaddr, dnsname, or other id.  this returns a Host object'
        ret = cls.hosts.get(hostid)
        if ret is None:
            ret = cls.hosts[hostid] = Host(hostid)
        return ret

    def __init__(self, addr=None):
        self.macaddr = None
        self.mac_manuf = None
        self.ipaddrs = set()

        if addr:
            if isinstance(addr, bytes):
                if len(addr) == 6:     # mac
                    self.setmac(addr)
                elif len(addr) == 4:   # ipv4
                    self.setip(addr)
                elif len(addr) == 16:  # ipv6
                    self.setip6(addr)
                else:
                    assert False, addr
            elif isinstance(addr, str):
                assert '.' in addr, addr
                self.sethostname(addr)
            else:
                assert False, addr

    def __str__(self):
        return self.hostname or self.ipaddr or self.macaddr

    def __lt__(self, x):
        return self.ipaddr < x.ipaddr

    def setmac(self, mac):
        if isinstance(mac, bytes):
            # Convert a MAC address to a readable/printable string
            mac = ':'.join('%02x' % b for b in mac)

        assert ':' in mac

        self.macaddr = mac
        self.mac_manuf = oui.get(mac[:13]) or oui.get(mac[:10]) or oui.get(mac[:8])

    def setip(self, ip):
        straddr = None
        if isinstance(ip, bytes):
            straddr = '.'.join('%d' % b for b in ip)
        elif isinstance(ip, str):
            straddr = addrbytes
        else:
            assert False, ip

        self.ipaddrs.add(straddr)

    @property
    def ipaddr(self):
        if len(self.ipaddrs) == 1:
            return list(self.ipaddrs)[0]

    @property
    def hostname(self):
        return self.dns.get(self.ipaddr)

def load_consts(outdict, module, attrprefix):
    for k in dir(module):
        if k.startswith(attrprefix):
            v = getattr(module, k)
            outdict[v] = k[len(attrprefix):]

def getTuple(pkt):
    if getattrdeep(pkt, 'ip.tcp'):
        tup = ('tcp', Host.get(pkt.ip.src), pkt.ip.tcp.sport, Host.get(pkt.ip.dst), pkt.ip.tcp.dport)
    elif getattrdeep(pkt, 'ip.udp'):
        tup = ('udp', Host.get(pkt.ip.src), pkt.ip.udp.sport, Host.get(pkt.ip.dst), pkt.ip.udp.dport)
    else:
        return None
    a,b,c,d,e = tup
    if b > d:
        return a,d,e,b,c  # swap src/sport and dst/dport
    else:
        return tup

def getService(tup):
    if not tup: return
    transport, _, sport, _, dport = tup
    if (transport, dport) in services:
        return services.get((transport, dport))
    if (transport, sport) in services:
        return services.get((transport, sport))


def show_dns(dns):
    for rr in dns.rr:
        if rr.rtype == 1:
            return '%s -> %s' % (rr.rname, rr.rdata)
    for q in dns.questions:
        return str(q.qname)

def get_transport(pkt):
    ret = 'ether'
    if getattr(pkt, 'ip', None):
        ret = 'ip'
        if getattr(pkt.ip, 'tcp', None):
            ret = 'tcp'
        elif getattr(pkt.ip, 'udp', None):
            ret = 'udp'
            if getattr(pkt, 'dns', None):
                ret = 'dns'
        elif getattr(pkt.ip, 'icmp', None):
            ret = 'icmp'
    elif getattr(pkt, 'arp', None):
        ret = 'arp'
    return ret

def get_srcport(pkt):
    ret = None
    if getattr(pkt, 'ip', None):
        if getattr(pkt.ip, 'tcp', None):
            ret = pkt.ip.tcp.sport
        elif getattr(pkt.ip, 'udp', None):
            ret = pkt.ip.udp.sport
    return ret

def get_dstport(pkt):
    ret = None
    if getattr(pkt, 'ip', None):
        if getattr(pkt.ip, 'tcp', None):
            ret = pkt.ip.tcp.dport
        elif getattr(pkt.ip, 'udp', None):
            ret = pkt.ip.udp.dport
    return ret

class DpktSheet(Sheet):
    rowtype = 'packets'
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%H:%M:%S.%f"),
        Column('transport', type=get_transport, width=5),
        ColumnAttr('src', type=Host.get),
        Column('srcport', type=get_srcport),
        ColumnAttr('dst', type=Host.get),
        Column('dstport', type=get_dstport),
#        Column('ether_manuf', getter=lambda col,row: mac_manuf(mac_addr(row.src))),
#        ColumnAttr('ether_src', 'src', type=mac_addr, width=6),
#        ColumnAttr('ether_dst', 'dst', type=mac_addr, width=6),
        ColumnAttr('ether_proto', 'type', type=lambda v: protocols['ethernet'].get(v), width=0),
#        ColumnAttr('ether_data', 'data', type=len, width=0),
#        ColumnAttr('ip', width=0),
#        ColumnAttr('ip_hdrlen', 'ip.hl', width=0, helpstr="IPv4 Header Length"),
#        ColumnAttr('ip_proto', 'ip.p', type=lambda v: protocols['ip'].get(v), width=8, helpstr="IPv4 Protocol"),
#        ColumnAttr('ip_id', 'ip.id', width=0, helpstr="IPv4 Identification"),
#        ColumnAttr('ip_rf', 'ip.rf', width=0, helpstr="IPv4 Reserved Flag (Evil Bit)"),
#        ColumnAttr('ip_df', 'ip.df', width=0, helpstr="IPv4 Don't Fragment flag"),
#        ColumnAttr('ip_mf', 'ip.mf', width=0, helpstr="IPv4 More Fragments flag"),
#        ColumnAttr('ip_tos', 'ip.tos', width=0, type=FlagGetter('ip_tos'), helpstr="IPv4 Type of Service"),
#        ColumnAttr('ip_ttl', 'ip.ttl', width=0, helpstr="IPv4 Time To Live"),
#        ColumnAttr('ip_ver', 'ip.v', width=0, helpstr="IPv4 Version"),
#        ColumnAttr('tcp', 'ip.tcp', width=4),
#        ColumnAttr('udp', 'ip.udp', width=4),
#        ColumnAttr('icmp', 'ip.icmp', width=4),
#        ColumnAttr('dns', width=4),
#        Column('dnsQ', getter=lambda col,row: show_dns(row.dns)),
#        ColumnAttr('netbios', width=4),
#        Column('ip_src', width=14, getter=lambda col,row: col.sheet.ip_addr(row.ip.src)),
#        Column('ip_dst', width=14, getter=lambda col,row: col.sheet.ip_addr(row.ip.dst)),
#        ColumnAttr('tcp_opts', 'ip.tcp.opts', width=0),
        ColumnAttr('tcp_flags', 'ip.tcp.flags', type=FlagGetter('tcp'), helpstr="TCP Flags"),
#        ColumnAttr('tcp_srcport', 'ip.tcp.sport', type=int, width=8, helpstr="TCP Source Port"),
#        ColumnAttr('tcp_dstport', 'ip.tcp.dport', type=int, width=8, helpstr="TCP Dest Port"),
#        Column('service', width=8, getter=lambda col,row: getService(getTuple(row)), helpstr="Service Abbr"),
#        ColumnAttr('udp_srcport', 'ip.udp.sport', type=int, width=8, helpstr="UDP Source Port"),
#        ColumnAttr('udp_dstport', 'ip.udp.dport', type=int, width=8, helpstr="UDP Dest Port"),
#        ColumnAttr('ip.udp.data', type=len, width=0),
#        ColumnAttr('ip.udp.ulen', type=int, width=0),
    ]


class PcapSheet(DpktSheet):
    @asyncthread
    def reload(self):
        init_pcap()

        f = self.source.open_bytes()
        self.pcap = dpkt.pcap.Reader(f)
        self.rows = []
        with Progress(total=self.source.filesize) as prog:
            for ts, buf in self.pcap:
                eth = dpkt.ethernet.Ethernet(buf)
                self.rows.append(eth)
                prog.addProgress(len(buf))

                eth.timestamp = ts
                if not getattr(eth, 'ip', None):
                    eth.ip = getattr(eth, 'ip6', None)
                eth.dns = try_apply(lambda eth: dnslib.DNSRecord.parse(eth.ip.udp.data), eth)
                if eth.dns:
                    for rr in eth.dns.rr:
                        Host.dns[str(rr.rdata)] = str(rr.rname)

                srchost = Host.get(eth.src)
                srcip = getattr(eth, 'ip', None)
                if srcip:
                    srchost.setip(srcip.src)

                dsthost = Host.get(eth.dst)
                dstip = getattr(eth, 'ip', None)
                if dstip:
                    dsthost.setip(dstip.src)

#                eth.netbios = try_apply(lambda eth: dpkt.netbios.NS(eth.ip.udp.data), eth)

PcapSheet.addCommand('1', 'flows', 'vd.push(PcapFlowsSheet("flows", source=sheet))')


flowtype = collections.namedtuple('flow', 'transport src sport dst dport packets'.split())

class PcapFlowsSheet(Sheet):
    rowtype = 'netflows'  # rowdef: flowtype
    columns = [
        ColumnAttr('transport'),
        ColumnAttr('src', type=Host.get),
        ColumnAttr('sport', type=int),
        ColumnAttr('dst', type=Host.get),
        ColumnAttr('dport', type=int),
        Column('service', width=8, getter=lambda col,row: getService(getTuple(row.packets[0]))),
        ColumnAttr('packets', type=len),
        Column('connect_latency_ms', type=float, getter=lambda col,row: col.sheet.latency[getTuple(row.packets[0])]),
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        self.flows = {}
        self.latency = {}  # [flowtuple] -> float ms of latency
        self.syntimes = {}  # [flowtuple] -> timestamp of SYN
        flags = FlagGetter('tcp')
        for pkt in self.source.rows:
            tup = getTuple(pkt)
            if tup:
                flowpkts = self.flows.get(tup)
                if flowpkts is None:
                    flowpkts = self.flows[tup] = []
                    self.addRow(flowtype(*tup, flowpkts))
                flowpkts.append(pkt)

                if not getattr(pkt.ip, 'tcp', None):
                    continue

                tcpfl = flags(pkt.ip.tcp.flags)
                if 'SYN' in tcpfl:
                    if 'ACK' in tcpfl:
                        if tup in self.syntimes:
                            self.latency[tup] = (pkt.timestamp - self.syntimes[tup])*1000
                    else:
                        self.syntimes[tup] = pkt.timestamp

PcapFlowsSheet.addCommand(ENTER, 'dive-row', 'vd.push(PcapSheet("%s_packets"%flowname(cursorRow), rows=cursorRow.packets))')

def flowname(flow):
    return '%s_%s:%s-%s:%s' % (flow.transport, Host.get(flow.src), flow.sport, Host.get(flow.dst), flow.dport)

def try_apply(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        pass


def open_pcap(p):
    return PcapSheet(p.name, source = p)
