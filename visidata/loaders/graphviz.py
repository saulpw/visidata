from visidata import options, option, exceptionCaught, TypedWrapper, asyncthread, Progress
from visidata import wrapply, clean_to_id, isNumeric

option('graphviz_edge_labels', True, 'whether to include edge labels on graphviz diagrams')


si_levels = ['', 'k', 'M', 'G', 'T', 'P', 'Q']
def SI(n):
    if not isinstance(n, (int, float)):
        return n
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

            downsrc = clean_to_id(str(src)) or src
            downdst = clean_to_id(str(dst)) or dst
            edgenotes = [c.getTypedValue(row) for c in vs.nonKeyVisibleCols if not isNumeric(c)]
            edgetype = '-'.join(str(x) for x in edgenotes if is_valid(x))
            color = assignedColors.get(edgetype, None)
            if not color:
                color = unusedColors.pop() if unusedColors else 'black'
                assignedColors[edgetype] = color

            if options.graphviz_edge_labels:
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
