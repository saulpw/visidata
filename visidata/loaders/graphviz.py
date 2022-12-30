from visidata import vd, options, TypedWrapper, asyncthread, Progress
from visidata import wrapply, clean_to_id, VisiData

vd.option('graphviz_edge_labels', True, 'whether to include edge labels on graphviz diagrams')


def is_valid(v):
    if v is None:
        return False
    if isinstance(v, TypedWrapper):
        return False
    return True


@VisiData.api
def save_dot(vd, p, vs):
    unusedColors = 'orange green purple cyan red blue black'.split()
    assignedColors = {}

    srccol = vs.keyCols[0]
    dstcol = vs.keyCols[1]
    with p.open_text(mode='w', encoding='utf-8') as fp:
        pfp = lambda *args: print(*args, file=fp)
        pfp('graph { concentrate=true;')
        for row in Progress(vs.rows, 'saving'):
            src = srccol.getTypedValue(row)
            dst = dstcol.getTypedValue(row)
            if not is_valid(src) or not is_valid(dst):
                continue

            downsrc = clean_to_id(str(src)) or src
            downdst = clean_to_id(str(dst)) or dst
            edgenotes = [c.getTypedValue(row) for c in vs.nonKeyVisibleCols if not vd.isNumeric(c)]
            edgetype = '-'.join(str(x) for x in edgenotes if is_valid(x))
            color = assignedColors.get(edgetype, None)
            if not color:
                color = unusedColors.pop() if unusedColors else 'black'
                assignedColors[edgetype] = color

            if options.graphviz_edge_labels:
                nodelabels = [wrapply(vd.SIFormatter, '%0.1f', c.getTypedValue(row)) for c in vs.nonKeyVisibleCols if vd.isNumeric(c)]
                label = '/'.join(str(x) for x in nodelabels if is_valid(x))
            else:
                label = ''
            pfp('\t%s[label="%s"];' % (downsrc, src))
            pfp('\t%s[label="%s"];' % (downdst, dst))
            pfp('\t%s -- %s[label="%s", color=%s];' % (downsrc, downdst, label, color))

        pfp('label="%s"' % vs.name)
        pfp('node[shape=plaintext];')
        pfp('subgraph cluster_legend {')
        pfp('label="Legend";')
        for i, (k, color) in enumerate(assignedColors.items()):
            pfp('key%d[label="%s", fontcolor=%s];' % (i, k, color))

        pfp('}')  # legend subgraph
        pfp('}')
