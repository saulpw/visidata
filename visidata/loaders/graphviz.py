from visidata import *
from namestand import downscore

option('pcap_internet', 'n', '(y/s/n) if save_dot includes all internet hosts separately (y), combined (s), or does not include the internet (n)')
option('pcap_edge_labels', True, 'whether to include pcap edge labels')

si_levels = ['', 'k', 'M', 'G', 'T', 'P', 'Q']
def SI(n):
    orig_n = n
    try:
        level = 0
        while n > 1000:
            n /= 1000
            level += 1
        return '%0.1f%s' % (n, si_levels[level])
    except Exception as e:
        exceptionCaught(e)
        return orig_n

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


def is_valid(v):
    if v is None:
        return False
    if isinstance(v, TypedWrapper):
        return False
    return True


@asyncthread
def save_dot(p, vs):
    unusedColors = 'orange green purple cyan red blue black'.split()
    assignedColors = {}

    srccol = vs.keyCols[0]
    dstcol = vs.keyCols[1]
    with p.open_text(mode='w') as fp:
        print('graph { concentrate=true;', file=fp)
        for row in Progress(vs.rows):
            src = srccol.getTypedValue(row)
            dst = dstcol.getTypedValue(row)
            if not is_valid(src) or not is_valid(dst):
                continue

            downsrc = downscore(str(src)) or src
            downdst = downscore(str(dst)) or dst
            edgetype = '-'.join(c.getTypedValue(row) for c in vs.nonKeyVisibleCols if not isNumeric(c))
            color = assignedColors.get(edgetype, None)
            if not color:
                color = assignedColors[edgetype] = unusedColors.pop()

            if options.pcap_edge_labels:
                nodelabels = [wrapply(SI, c.getTypedValue(row)) for c in vs.nonKeyVisibleCols if isNumeric(c)]
                label = '/'.join(str(x) for x in nodelabels if is_valid(x))
            else:
                label = ''
            print('\t%s[label="%s"];' % (downsrc, src), file=fp)
            print('\t%s[label="%s"];' % (downdst, dst), file=fp)
            print('\t%s -- %s[label="%s", color=%s];' % (downsrc, downdst, label, color), file=fp)

        print('label="%s"' % vs.name, file=fp)
        print('node[shape=plaintext];', file=fp)
        print('subgraph cluster_legend {', file=fp)
        print('label="Legend";', file=fp)
        for i, (k, color) in enumerate(assignedColors.items()):
            print('key%d[label="%s", fontcolor=%s];' % (i, k, color), file=fp)

        print('}', file=fp)  # legend subgraph
        print('}', file=fp)
