'''
Add plot-column-ext and plot-numerics-ext to Sheet, and plot-ext to GraphSheet, to open current graph in new matplotlib window.
'''

from visidata import vd, VisiData, Sheet, GraphSheet, Progress, asyncthread

@VisiData.api
@asyncthread
def plot_seaborn(vd, rows, xcols, ycols):
    vd.status(f'plotting {len(rows)} rows using matplotlib')
    import multiprocessing
    mp = multiprocessing.Process(target=ext_plot_seaborn, args=(rows, xcols, ycols))
    mp.start()


def ext_plot_seaborn(rows, xcols, ycols):
    pd = vd.importExternal('pandas')
    plt = vd.importExternal('matplotlib.pyplot', 'matplotlib')
    sns = vd.importExternal('seaborn')

    # Set the default theme
    sns.set()

    plt.figure(figsize=(10, 6))
    plt.title('')
    plt.xticks(rotation=15)

    nerrors = 0
    nplotted = 0

    x_array = []
    y_array = []
    cat_array = []

    catcols = [c for c in xcols if not vd.isNumeric(c)]
    numcols = vd.numericCols(xcols)
    for rownum, row in enumerate(Progress(rows, 'plotting')):
        for ycol in ycols:
            try:
                if catcols:
                    k = tuple(c.getValue(row) for c in catcols)
                    if len(catcols) == 1:
                        k = k[0]
                else:
                    k = ycol.name

                graph_x = numcols[0].type(numcols[0].getValue(row)) if numcols else rownum
                graph_y = ycol.type(ycol.getValue(row))

                x_array.append(graph_x)
                y_array.append(graph_y)
                cat_array.append(k)

                nplotted += 1
            except Exception:
                nerrors += 1
                if vd.options.debug:
                    raise

    sns.scatterplot(
        x=x_array,
        y=y_array,
        hue=cat_array,
#        hue_order=df.tag.value_counts().iloc[:top].index,
#        data=tmpdf,
        s=5,
        linewidth=0,
        ).legend().set_title = (None)

    plt.show()


Sheet.addCommand('', 'plot-column-ext', 'plot_seaborn(rows, keyCols, numericCols([cursorCol]))', 'plot current numeric column on y-axis vs key columns on x-axis using matplotlib/seaborn')
Sheet.addCommand('', 'plot-numerics-ext', 'plot_seaborn(rows, keyCols, numericCols(nonKeyVisibleCols))', 'plot a graph of all visible numeric columns using matplotlib/seaborn')
GraphSheet.addCommand('', 'plot-ext', 'plot_seaborn(sourceRows, xcols, ycols)', 'replot current graph using matplotlib/seaborn')

vd.addMenuItem('Plot', 'Graph', 'using matplotlib', 'current column', 'plot-column-ext')
vd.addMenuItem('Plot', 'Graph', 'using matplotlib', 'all numeric columns', 'plot-numerics-ext')
vd.addMenuItem('Plot', 'Graph', 'replot using matplotlib', 'plot-ext')
