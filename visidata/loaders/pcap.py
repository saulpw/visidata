import collections
import ipaddress

from visidata import VisiData, vd, Sheet, options, Column, asyncthread, Progress, TsvSheet, getattrdeep, ColumnAttr, date, vlen, filesize

vd.option('pcap_internet', 'n', '(y/s/n) if save_dot includes all internet hosts separately (y), combined (s), or does not include the internet (n)')

protocols = collections.defaultdict(dict)  # ['ethernet'] = {[6] -> 'IP'}
_flags = collections.defaultdict(dict)  # ['tcp'] = {[4] -> 'FIN'}


url_oui = 'https://visidata.org/plugins/pcap/wireshark-oui.tsv'
url_iana = 'https://visidata.org/plugins/pcap/iana-ports.tsv'

oui = {}  # [macprefix (like '01:02:dd:0')] -> 'manufacturer'
services = {}  # [('tcp', 25)] -> 'smtp'

@VisiData.api
def open_pcap(vd, p):
    return PcapSheet(p.name, source=p)

open_cap = open_pcap
open_pcapng = open_pcap
open_ntar = open_pcap

def manuf(mac):
    return oui.get(mac[:13]) or oui.get(mac[:10]) or oui.get(mac[:8])

def macaddr(addrbytes):
    mac = ':'.join('%02x' % b for b in addrbytes)
    return mac

def macmanuf(mac):
    manuf = oui.get(mac[:13])
    if manuf:
        return manuf + mac[13:]

    manuf = oui.get(mac[:10])
    if manuf:
        return manuf + mac[10:]

    manuf = oui.get(mac[:8])
    if manuf:
        return manuf + mac[8:]

    return mac


def norm_host(host):
    if not host:
        return None
    srcmac = str(host.macaddr)
    if srcmac == 'ff:ff:ff:ff:ff:ff': return None

    srcip = str(host.ipaddr)
    if srcip == '0.0.0.0' or srcip == '::': return None
    if srcip == '255.255.255.255': return None

    if host.ipaddr:
        if host.ipaddr.is_global:
            opt = options.pcap_internet
            if opt == 'n':
                return None
            elif opt == 's':
                return "internet"

        if host.ipaddr.is_multicast:
            # include in multicast  (minus dns?)
            return 'multicast'

    names = [host.hostname, host.ipaddr, macmanuf(host.macaddr)]
    return '\\n'.join(str(x) for x in names if x)


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

    load_oui(url_oui)
    load_iana(url_iana)


def read_pcap(f):

    try:
        return dpkt.pcapng.Reader(f.open_bytes())
    except ValueError:
        return dpkt.pcap.Reader(f.open_bytes())


@asyncthread
def load_oui(url):
    vsoui = TsvSheet('vsoui', source=vd.urlcache(url, days=30))
    vsoui.reload.__wrapped__(vsoui)
    for r in vsoui.rows:
        if r.prefix.endswith('/36'): prefix = r.prefix[:13]
        elif r.prefix.endswith('/28'): prefix = r.prefix[:10]
        else: prefix = r.prefix[:8]
        try:
            oui[prefix.lower()] = r.shortname
        except Exception as e:
            vd.exceptionCaught(e)


@asyncthread
def load_iana(url):
    ports_tsv = TsvSheet('ports_tsv', source=vd.urlcache(url, days=30))
    ports_tsv.reload.__wrapped__(ports_tsv)
    for r in ports_tsv.rows:
        try:
            services[(r.transport, int(r.port))] = r.service
        except Exception as e:
            vd.exceptionCaught(e)


class Host:
    dns = {}  # [ipstr] -> dnsname
    hosts = {}  # [macaddr] -> { [ipaddr] -> Host }

    @classmethod
    def get_host(cls, pkt, field='src'):
        mac = macaddr(getattr(pkt, field))
        machosts = cls.hosts.get(mac, None)
        if not machosts:
            machosts = cls.hosts[mac] = {}

        ipraw = getattrdeep(pkt, 'ip.'+field, None)
        if ipraw is not None:
            ip = ipaddress.ip_address(ipraw)
            if ip not in machosts:
                machosts[ip] = Host(mac, ip)
            return machosts[ip]
        else:
            if machosts:
                return list(machosts.values())[0]

        return Host(mac, None)

    @classmethod
    def get_by_ip(cls, ip):
        'Returns Host instance for the given ip address.'
        ret = cls.hosts_by_ip.get(ip)
        if ret is None:
            ret = cls.hosts_by_ip[ip] = [Host(ip)]
        return ret

    def __init__(self, mac, ip):
        self.ipaddr = ip
        self.macaddr = mac
        self.mac_manuf = None

    def __str__(self):
        return str(self.hostname or self.ipaddr or macmanuf(self.macaddr))

    def __lt__(self, x):
        if isinstance(x, Host):
            return str(self.ipaddr) < str(x.ipaddr)
        return True

    @property
    def hostname(self):
        return Host.dns.get(str(self.ipaddr))

def load_consts(outdict, module, attrprefix):
    for k in dir(module):
        if k.startswith(attrprefix):
            v = getattr(module, k)
            outdict[v] = k[len(attrprefix):]

def getTuple(pkt):
    if getattrdeep(pkt, 'ip.tcp', None):
        tup = ('tcp', Host.get_host(pkt, 'src'), pkt.ip.tcp.sport, Host.get_host(pkt, 'dst'), pkt.ip.tcp.dport)
    elif getattrdeep(pkt, 'ip.udp', None):
        tup = ('udp', Host.get_host(pkt, 'src'), pkt.ip.udp.sport, Host.get_host(pkt, 'dst'), pkt.ip.udp.dport)
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


def get_transport(pkt):
    ret = 'ether'
    if getattr(pkt, 'arp', None):
        return 'arp'

    if getattr(pkt, 'ip', None):
        ret = 'ip'
        if getattr(pkt.ip, 'tcp', None):
            ret = 'tcp'
        elif getattr(pkt.ip, 'udp', None):
            ret = 'udp'
        elif getattr(pkt.ip, 'icmp', None):
            ret = 'icmp'

    if getattr(pkt, 'ip6', None):
        ret = 'ipv6'
        if getattr(pkt.ip6, 'tcp', None):
            ret = 'tcp'
        elif getattr(pkt.ip6, 'udp', None):
            ret = 'udp'
        elif getattr(pkt.ip6, 'icmp6', None):
            ret = 'icmpv6'

    return ret


def get_port(pkt, field='sport'):
    return getattrdeep(pkt, 'ip.tcp.'+field, None) or getattrdeep(pkt, 'ip.udp.'+field, None)


class EtherSheet(Sheet):
    'Layer 2 (ethernet) packets'
    rowtype = 'packets'
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%H:%M:%S.%f"),
        Column('ether_manuf', type=str, getter=lambda col,row: mac_manuf(macaddr(row.src))),
        Column('ether_src', type=str, getter=lambda col,row: macaddr(row.src), width=6),
        Column('ether_dst', type=str, getter=lambda col,row: macaddr(row.dst), width=6),
        ColumnAttr('ether_data', 'data', type=vlen, width=0),
    ]


@VisiData.api
class IPSheet(Sheet):
    rowtype = 'packets'
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%H:%M:%S.%f"),
        ColumnAttr('ip', type=str, width=0),
        Column('ip_src', type=str, width=14, getter=lambda col,row: ipaddress.ip_address(row.ip.src)),
        Column('ip_dst', type=str, width=14, getter=lambda col,row: ipaddress.ip_address(row.ip.dst)),
        ColumnAttr('ip_hdrlen', 'ip.hl', type=int, width=0, helpstr="IPv4 Header Length"),
        ColumnAttr('ip_proto', 'ip.p', type=lambda v: protocols['ip'].get(v), width=8, helpstr="IPv4 Protocol"),
        ColumnAttr('ip_id', 'ip.id', type=int, width=10, helpstr="IPv4 Identification"),
        ColumnAttr('ip_rf', 'ip.rf', type=int, width=10, helpstr="IPv4 Reserved Flag (Evil Bit)"),
        ColumnAttr('ip_df', 'ip.df', type=int, width=10, helpstr="IPv4 Don't Fragment flag"),
        ColumnAttr('ip_mf', 'ip.mf', type=int, width=10, helpstr="IPv4 More Fragments flag"),
        ColumnAttr('ip_tos', 'ip.tos', width=10, type=FlagGetter('ip_tos'), helpstr="IPv4 Type of Service"),
        ColumnAttr('ip_ttl', 'ip.ttl', type=int, width=10, helpstr="IPv4 Time To Live"),
        ColumnAttr('ip_ver', 'ip.v', type=int, width=10, helpstr="IPv4 Version"),
    ]

    def iterload(self):
        for pkt in Progress(self.source.rows):
            if getattr(pkt, 'ip', None):
                yield pkt


@VisiData.api
class TCPSheet(IPSheet):
    columns = IPSheet.columns + [
        ColumnAttr('tcp_srcport', 'ip.tcp.sport', type=int, width=8, helpstr="TCP Source Port"),
        ColumnAttr('tcp_dstport', 'ip.tcp.dport', type=int, width=8, helpstr="TCP Dest Port"),
        ColumnAttr('tcp_opts', 'ip.tcp.opts', width=0),
        ColumnAttr('tcp_flags', 'ip.tcp.flags', type=FlagGetter('tcp'), helpstr="TCP Flags"),
    ]

    def iterload(self):
        for pkt in Progress(self.source.rows):
            if getattrdeep(pkt, 'ip.tcp', None):
                yield pkt

class UDPSheet(IPSheet):
    columns = IPSheet.columns + [
        ColumnAttr('udp_srcport', 'ip.udp.sport', type=int, width=8, helpstr="UDP Source Port"),
        ColumnAttr('udp_dstport', 'ip.udp.dport', type=int, width=8, helpstr="UDP Dest Port"),
        ColumnAttr('ip.udp.data', type=vlen, width=0),
        ColumnAttr('ip.udp.ulen', type=int, width=0),
    ]

    def iterload(self):
        for pkt in Progress(self.source.rows):
            if getattrdeep(pkt, 'ip.udp', None):
                yield pkt


class PcapSheet(Sheet):
    rowtype = 'packets'
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%H:%M:%S.%f"),
        Column('transport', type=get_transport, width=5),
        Column('srcmanuf', type=str, getter=lambda col,row: manuf(macaddr(row.src))),
        Column('srchost', type=str, getter=lambda col,row: row.srchost),
        Column('srcport', type=int, getter=lambda col,row: get_port(row, 'sport')),
        Column('dstmanuf', type=str, getter=lambda col,row: manuf(macaddr(row.dst))),
        Column('dsthost', type=str, getter=lambda col,row: row.dsthost),
        Column('dstport', type=int, getter=lambda col,row: get_port(row, 'dport')),
        ColumnAttr('ether_proto', 'type', type=lambda v: protocols['ethernet'].get(v), width=0),
        ColumnAttr('tcp_flags', 'ip.tcp.flags', type=FlagGetter('tcp'), helpstr="TCP Flags"),
        Column('service', type=str, getter=lambda col,row: getService(getTuple(row))),
        ColumnAttr('data', type=vlen),
        ColumnAttr('ip_len', 'ip.len', type=int),
        ColumnAttr('tcp', 'ip.tcp', width=4, type=vlen),
        ColumnAttr('udp', 'ip.udp', width=4, type=vlen),
        ColumnAttr('icmp', 'ip.icmp', width=4, type=vlen),
        ColumnAttr('dns', type=str, width=4),
    ]

    def iterload(self):
        init_pcap()

        self.pcap = read_pcap(self.source)
        self.rows = []
        with Progress(total=filesize(self.source)) as prog:
            for ts, buf in self.pcap:
                eth = dpkt.ethernet.Ethernet(buf)
                yield eth
                prog.addProgress(len(buf))

                eth.timestamp = ts
                if not getattr(eth, 'ip', None):
                    eth.ip = getattr(eth, 'ip6', None)
                eth.dns = try_apply(lambda eth: dnslib.DNSRecord.parse(eth.ip.udp.data), eth)
                if eth.dns:
                    for rr in eth.dns.rr:
                        Host.dns[str(rr.rdata)] = str(rr.rname)

                eth.srchost = Host.get_host(eth, 'src')
                eth.dsthost = Host.get_host(eth, 'dst')




flowtype = collections.namedtuple('flow', 'packets transport src sport dst dport'.split())

@VisiData.api
class PcapFlowsSheet(Sheet):
    rowtype = 'netflows'  # rowdef: flowtype
    _rowtype = flowtype

    columns = [
        ColumnAttr('transport', type=str),
        Column('src', type=str, getter=lambda col,row: row.src),
        ColumnAttr('sport', type=int),
        Column('dst', type=str, getter=lambda col,row: row.dst),
        ColumnAttr('dport', type=int),
        Column('service', type=str, width=8, getter=lambda col,row: getService(getTuple(row.packets[0]))),
        ColumnAttr('packets', type=vlen),
        Column('connect_latency_ms', type=float, getter=lambda col,row: col.sheet.latency[getTuple(row.packets[0])]),
    ]

    def iterload(self):
        self.flows = {}
        self.latency = {}  # [flowtuple] -> float ms of latency
        self.syntimes = {}  # [flowtuple] -> timestamp of SYN
        flags = FlagGetter('tcp')
        for pkt in Progress(self.source.rows):
            tup = getTuple(pkt)
            if tup:
                flowpkts = self.flows.get(tup)
                if flowpkts is None:
                    flowpkts = self.flows[tup] = []
                    yield flowtype(flowpkts, *tup)
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

    def openRow(self, row):
        return PcapSheet("%s_packets"%flowname(row), rows=row.packets)


def flowname(flow):
    return '%s_%s:%s-%s:%s' % (flow.transport, flow.src, flow.sport, flow.dst, flow.dport)

def try_apply(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        pass


PcapSheet.addCommand('W', 'flows', 'vd.push(PcapFlowsSheet(sheet.name+"_flows", source=sheet))')
PcapSheet.addCommand('2', 'l2-packet', 'vd.push(IPSheet("L2packets", source=sheet))')
PcapSheet.addCommand('3', 'l3-packet', 'vd.push(TCPSheet("L3packets", source=sheet))')

vd.addMenuItem('View', 'Packet capture', 'flows', 'flows')
vd.addMenuItem('View', 'Packet capture', 'IP (L2)', 'l2-packet')
vd.addMenuItem('View', 'Packet capture', 'TCP (L3)', 'l3-packet')
