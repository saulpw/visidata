from visidata import *

@GraphSheet.api
def plot_async(sheet):
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    nerrors = 0
    nplotted = 0

    x_array = []
    y_array = []
    cat_array = []

    catcols = [c for c in sheet.xcols if not vd.isNumeric(c)]
    numcols = vd.numericCols(sheet.xcols)
    for rownum, row in enumerate(Progress(sheet.sourceRows, 'plotting')):  # rows being plotted from source
        for ycol in sheet.ycols:
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
                if options.debug:
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


@GraphSheet.api
def plotsea(sheet):
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 6))
    plt.title('')
    plt.xticks(rotation=15)

    sheet.plot_async()

    plt.show()


GraphSheet.addCommand('.', 'plot-seaborn', 'plotsea()', 'plot current graph using matplotlib/seaborn')
vd.addMenuItem('Plot', 'Graph', '+using matplotlib', 'plot-seaborn')
