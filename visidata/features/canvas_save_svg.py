'''
Add svg saver to Canvas.

Requires matplotlib.pyplot
'''


import collections

from visidata import VisiData, Canvas, vd, Progress

vd.option('plt_marker', '.', 'matplotlib.markers')


@Canvas.api
def plot_sheet(self, ax):
    plt = vd.importExternal('matplotlib.pyplot', 'matplotlib')
    nerrors = 0
    nplotted = 0

    self.reset()

    vd.status('loading data points')
    catcols = [c for c in self.xcols if not vd.isNumeric(c)]
    numcols = [c for c in self.xcols if vd.isNumeric(c)]
    for ycol in self.ycols:
        xpts = collections.defaultdict(list)
        ypts = collections.defaultdict(list)
        for rownum, row in enumerate(Progress(self.sourceRows, 'plotting')):  # rows being plotted from source
            try:
                k = tuple(c.getValue(row) for c in catcols) if catcols else (ycol.name,)

                # convert deliberately to float (to e.g. linearize date)
                graph_x = numcols[0].type(numcols[0].getValue(row)) if numcols else rownum
                graph_y = ycol.type(ycol.getValue(row))

                xpts[k].append(graph_x)
                ypts[k].append(graph_y)

                nplotted += 1
            except Exception:
                nerrors += 1
                if vd.options.debug:
                    raise
        lines = []
        for k in xpts:
            line = ax.scatter(xpts[k], ypts[k], label=' '.join(str(x) for x in k), **vd.options.getall('plt_'))
            lines.append(line)

        ax.legend(handles=lines)
        ax.set_xlabel(','.join(xcol.name for xcol in self.xcols if vd.isNumeric(xcol)) or 'row#')
        ax.xaxis.set_major_locator(plt.MaxNLocator(4))
        ax.yaxis.set_major_locator(plt.MaxNLocator(4))


@VisiData.api
def save_svg(vd, p, *sheets):
    plt = vd.importExternal('matplotlib.pyplot', 'matplotlib')
    fig_, ax = plt.subplots()
    for vs in sheets:
        if not isinstance(vs, Canvas):
            vd.warning(f'{vs.name} not a Canvas')
            continue
        vs.plot_sheet(ax)

    ax.grid()
    ax.set_title('\n'.join(vs.name for vs in sheets))
    plt.xticks()
    plt.savefig(p, format='svg')
