import struct
import collections
import functools

from visidata import *

def _ord(c):
    return struct.unpack('B', c)[0]

def mac_addr(address):
    'Convert a MAC address to a readable/printable string'
    return ':'.join('%02x' % b for b in address)

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

    vsoui = open_tsv(Path('wireshark-oui.tsv'))
    vsoui.reload_sync()
    for macslash, shortname, _ in vsoui.rows:
        if macslash.endswith('/36'): prefix = macslash[:13]
        elif macslash.endswith('/28'): prefix = macslash[:13]
        else: prefix = macslash[:13]
        oui[prefix.lower()] = shortname

    ports_tsv = open_tsv(Path('iana-ports.tsv'))
    ports_tsv.reload_sync()
    for r in ports_tsv.rows:
        services[(r.transport, int(r.port))] = r.service


def mac_manuf(mac):
    return oui.get(mac[:13]) or oui.get(mac[:10]) or oui.get(mac[:8])

def load_consts(outdict, module, attrprefix):
    for k in dir(module):
        if k.startswith(attrprefix):
            v = getattr(module, k)
            outdict[v] = k[len(attrprefix):]

def getTuple(pkt):
    if getattrdeep(pkt, 'ip.tcp'):
        tup = ('tcp', DpktSheet.ip_addr(pkt.ip.src), pkt.ip.tcp.sport, DpktSheet.ip_addr(pkt.ip.dst), pkt.ip.tcp.dport)
    elif getattrdeep(pkt, 'ip.udp'):
        tup = ('udp', DpktSheet.ip_addr(pkt.ip.src), pkt.ip.udp.sport, DpktSheet.ip_addr(pkt.ip.dst), pkt.ip.udp.dport)
    else:
        return None
    a,b,c,d,e = tup
    if b > d:
        return a,d,c,b,e
    else:
        return tup

def getService(tup):
    if not tup: return
    transport, _, sport, _, dport = tup
    if (transport, dport) in services:
        return services.get((transport, dport))
    if (transport, sport) in services:
        return services.get((transport, sport))


class DpktSheet(Sheet):
    rowtype = 'packets'
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%H:%M:%S.%f"),
        Column('ether_manuf', getter=lambda col,row: mac_manuf(mac_addr(row.src))),
        ColumnAttr('ether_src', 'src', type=mac_addr, width=6),
        ColumnAttr('ether_dst', 'dst', type=mac_addr, width=6),
        ColumnAttr('ether_proto', 'type', type=lambda v: protocols['ethernet'].get(v), width=5),
        ColumnAttr('ether_data', 'data', type=len, width=0),
        ColumnAttr('ip', width=0),
        ColumnAttr('ip_hdrlen', 'ip.hl', width=0, helpstr="IPv4 Header Length"),
        ColumnAttr('ip_proto', 'ip.p', type=lambda v: protocols['ip'].get(v), width=8, helpstr="IPv4 Protocol"),
        ColumnAttr('ip_id', 'ip.id', width=0, helpstr="IPv4 Identification"),
        ColumnAttr('ip_rf', 'ip.rf', width=0, helpstr="IPv4 Reserved Flag (Evil Bit)"),
        ColumnAttr('ip_df', 'ip.df', width=0, helpstr="IPv4 Don't Fragment flag"),
        ColumnAttr('ip_mf', 'ip.mf', width=0, helpstr="IPv4 More Fragments flag"),
        ColumnAttr('ip_tos', 'ip.tos', width=0, type=FlagGetter('ip_tos'), helpstr="IPv4 Type of Service"),
        ColumnAttr('ip_ttl', 'ip.ttl', width=0, helpstr="IPv4 Time To Live"),
#        ColumnAttr('ip_ver', 'ip.v', width=0, helpstr="IPv4 Version"),
        ColumnAttr('tcp', 'ip.tcp', width=0),
        ColumnAttr('udp', 'ip.udp', width=0),
        ColumnAttr('icmp', 'ip.icmp', width=0),
        ColumnAttr('dns'),
        ColumnAttr('netbios'),
        Column('ip_src', width=14, getter=lambda col,row: col.sheet.ip_addr(row.ip.src)),
        Column('ip_dst', width=14, getter=lambda col,row: col.sheet.ip_addr(row.ip.dst)),
        ColumnAttr('tcp_opts', 'ip.tcp.opts', width=0),
        ColumnAttr('tcp_flags', 'ip.tcp.flags', type=FlagGetter('tcp'), helpstr="TCP Flags"),
        ColumnAttr('tcp_srcport', 'ip.tcp.sport', type=int, width=8, helpstr="TCP Source Port"),
        ColumnAttr('tcp_dstport', 'ip.tcp.dport', type=int, width=8, helpstr="TCP Dest Port"),
        Column('service', width=8, getter=lambda col,row: getService(getTuple(row)), helpstr="Service Abbr"),
        ColumnAttr('udp_srcport', 'ip.udp.sport', type=int, width=8, helpstr="UDP Source Port"),
        ColumnAttr('udp_dstport', 'ip.udp.dport', type=int, width=8, helpstr="UDP Dest Port"),
        ColumnAttr('ip.udp.data', type=len, width=0),
        ColumnAttr('ip.udp.ulen', type=int, width=0),
    ]

    dns = {}  # [ipstr] -> dnsname

    @classmethod
    def ip_addr(cls, addrbytes):
        dottedquad = '.'.join('%d' % b for b in addrbytes)
        return cls.dns.get(dottedquad, dottedquad)


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
#                if eth.dns:
#                    for rr in eth.dns.rr:
#                        self.dns[str(rr.rdata)] = str(rr.rname)

#                eth.netbios = try_apply(lambda eth: dpkt.netbios.NS(eth.ip.udp.data), eth)

PcapSheet.addCommand('1', 'flows', 'vd.push(PcapFlowsSheet("flows", source=sheet))')


flowtype = collections.namedtuple('flow', 'transport src sport dst dport packets'.split())

class PcapFlowsSheet(Sheet):
    rowtype = 'netflows'  # rowdef: flowtype
    columns = [
        ColumnAttr('transport'),
        ColumnAttr('src', type=DpktSheet.ip_addr),
        ColumnAttr('sport', type=int),
        ColumnAttr('dst', type=DpktSheet.ip_addr),
        ColumnAttr('dport', type=int),
        Column('service', width=8, getter=lambda col,row: getService(getTuple(row.packets[0]))),
        ColumnAttr('packets', type=len),
        Column('connect_latency', getter=lambda col,row: col.sheet.latency[getTuple(row.packets[0])]),
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        self.flows = {}
        self.latency = {}  # [flowtuple] -> float seconds of latency
        syntimes = {}  # [flowtuple] -> timestamp of SYN
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
                        if tup in syntimes:
                            self.latency[tup] = pkt.timestamp - syntimes[tup]
                        else:
                            self.latency[tup] = 'wtf'
                    else:
                        syntimes[tup] = pkt.timestamp

PcapFlowsSheet.addCommand(ENTER, 'dive-row', 'vd.push(PcapSheet("%s_packets"%flowname(cursorRow), rows=cursorRow.packets))')

def flowname(flow):
    return '%s_%s:%s-%s:%s' % (flow.transport, DpktSheet.ip_addr(flow.src), flow.sport, DpktSheet.ip_addr(flow.dst), flow.dport)

def try_apply(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        pass


def open_pcap(p):
    return PcapSheet(p.name, source = p)
