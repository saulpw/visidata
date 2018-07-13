import dpkt
import struct

from visidata import *

def _ord(c):
    return struct.unpack('B', c)[0]

def mac_addr(address):
    """Convert a MAC address to a readable/printable string
    """
    return ':'.join('%02x' % b for b in address)

class PCAPSheet(Sheet):
    # @todo get columns from __hdr_fields__ and set getter for special cases
    columns = [
        Column('dst', getter=lambda col, row: mac_addr(row.dst)),
        Column('src', getter=lambda col, row: mac_addr(row.src)),
        ColumnAttr('type'),
        ColumnAttr('data'),
    ]

    def reload(self):
        f = self.source.open_bytes()
        pcap = dpkt.pcap.Reader(f)
        self.rows = []
        for ts, buf in pcap:
            eth = dpkt.ethernet.Ethernet(buf)
            self.rows.append(eth)

def open_pcap(p):
    return PCAPSheet(p.name, source = p)
