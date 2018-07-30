import struct

from visidata import *

def _ord(c):
    return struct.unpack('B', c)[0]

def mac_addr(address):
    """Convert a MAC address to a readable/printable string
    """
    return ':'.join('%02x' % b for b in address)

def ip_addr(address):
    return '.'.join('%d' % b for b in address)

eth_types = {}

def eth_type(v):
    return eth_types.get(v)

class PCAPSheet(Sheet):
    # @todo get columns from __hdr_fields__ and set getter for special cases
    columns = [
        ColumnAttr('timestamp', type=date, fmtstr="%Y-%m-%d %H:%M:%S"),
        ColumnAttr('ether_src', 'src', type=mac_addr),
        ColumnAttr('ether_dst', 'dst', type=mac_addr),
        ColumnAttr('ether_type', 'type', type=eth_type),
        ColumnAttr('ether_data', 'data', type=len),
        ColumnAttr('ip', width=0),
        ColumnAttr('ip_hdrlen', 'ip.hl', width=0, helpstr="IPv4 Header Length"),
        ColumnAttr('ip_p', 'ip.p', width=0, helpstr="IPv4 Protocol"),
        ColumnAttr('ip_id', 'ip.id', width=0, helpstr="IPv4 Identification"),
        ColumnAttr('ip_rf', 'ip.rf', width=0, helpstr="IPv4 Reserved Flag (Evil Bit)"),
        ColumnAttr('ip_df', 'ip.df', width=0, helpstr="IPv4 Don't Fragment flag"),
        ColumnAttr('ip_mf', 'ip.mf', width=0, helpstr="IPv4 More Fragments flag"),
        ColumnAttr('ip_tos', 'ip.tos', width=0, helpstr="IPv4 Type of Service"),
        ColumnAttr('ip_ttl', 'ip.ttl', width=0, helpstr="IPv4 Time To Live"),
#        ColumnAttr('ip_ver', 'ip.v', width=0, helpstr="IPv4 Version"),
        ColumnAttr('ip.tcp', width=0),
        ColumnAttr('ip.udp', width=0),
        ColumnAttr('ip.icmp', width=0),
        ColumnAttr('ip.src', type=ip_addr),
        ColumnAttr('ip.dst', type=ip_addr),
        ColumnAttr('tcp_srcport', 'ip.tcp.sport', type=int, helpstr="TCP Source Port"),
        ColumnAttr('tcp_dstport', 'ip.tcp.dport', type=int, helpstr="TCP Dest Port"),
        ColumnAttr('udp_srcport', 'ip.udp.sport', type=int, helpstr="UDP Source Port"),
        ColumnAttr('udp_dstport', 'ip.udp.dport', type=int, helpstr="UDP Dest Port"),
        ColumnAttr('ip.udp.data', type=len),
        ColumnAttr('ip.udp.ulen', type=int),
        ColumnAttr('ip6.dst', type=mac_addr),
    ]

    def reload(self):
        import dpkt

        global eth_types
        eth_types = {getattr(dpkt.ethernet, k):k[9:] for k in dir(dpkt.ethernet) if k.startswith('ETH_TYPE')}

        f = self.source.open_bytes()
        pcap = dpkt.pcap.Reader(f)
        self.rows = []
        for ts, buf in pcap:
            eth = dpkt.ethernet.Ethernet(buf)
            eth.timestamp = ts
            self.rows.append(eth)

def open_pcap(p):
    return PCAPSheet(p.name, source = p)
