from visidata import *

option('color_graph_axis', 'bold', 'color for graph axis labels')

globalCommand('m', 'vd.push(GraphSheet(sheet.name+"_graph", sheet, selectedRows or rows, keyCols, [cursorCol]))', 'graph the current column vs the first key column (or row number)')
globalCommand('gm', 'vd.push(GraphSheet(sheet.name+"_graph", sheet, selectedRows or rows, keyCols, numericCols(nonKeyVisibleCols)))', 'graph all numeric columns vs the first key column (or row number)')


def numericCols(cols):
    # isNumeric from describe.py
    return [c for c in cols if isNumeric(c)]


# provides unit->pixel conversion, axis labels, legend
class GraphSheet(GridCanvas):
    graphColornames = 'green red yellow cyan magenta white 38 136 168'.split()
    commands = GridCanvas.commands + [
        # swap directions of up/down
        Command('move-up', 'sheet.cursorGridTop += cursorGridHeight', ''),
        Command('move-down', 'sheet.cursorGridTop -= cursorGridHeight', ''),

        Command('zj', 'sheet.cursorGridTop -= charGridHeight', ''),
        Command('zk', 'sheet.cursorGridTop += charGridHeight', ''),

        Command('J', 'sheet.cursorGridHeight -= charGridHeight', ''),
        Command('K', 'sheet.cursorGridHeight += charGridHeight', ''),

        Command('zz', 'fixPoint(gridCanvasLeft, gridCanvasHeight, cursorGridLeft, cursorGridTop); sheet.visibleGridWidth=cursorGridWidth; sheet.visibleGridHeight=cursorGridHeight', 'set bounds to cursor'),
    ]

    def __init__(self, name, sheet, rows, xcols, ycols, **kwargs):
        self.graphColors = itertools.cycle([colors[colorname] for colorname in self.graphColornames])
        super().__init__(name, sheet, sourceRows=rows, **kwargs)

        self.xcols = xcols
        self.ycols = [ycol for ycol in ycols if isNumeric(ycol)] or error('%s is non-numeric' % '/'.join(yc.name for yc in ycols))
        self.legends = {}  # txt: attr

    def plotlegend(self, i, txt, attr):
        self.plotlabel(self.canvasWidth-30, i*4, txt, attr)

    def scaleY(self, grid_y):
        'returns canvas y coordinate, with y-axis inverted'
        canvas_y = super().scaleY(grid_y)
        return (self.gridCanvasBottom-canvas_y+4)

    def gridY(self, canvas_y):
        return (self.gridCanvasBottom-canvas_y)*self.visibleGridHeight/self.gridCanvasHeight

    @property
    def gridMouseY(self):
        return self.visibleGridTop + (self.gridCanvasBottom-self.canvasMouseY)*self.visibleGridHeight/self.gridCanvasHeight

    @property
    def cursorPixelBounds(self):
        x1, y1, x2, y2 = super().cursorPixelBounds
        return x1, y2, x2, y1  # reverse top/bottom

    @async
    def reload(self):
        nerrors = 0
        nplotted = 0

        self.gridpoints.clear()
        self.legends.clear()

        status('loading data points')
        catcols = [c for c in self.xcols if not isNumeric(c)]
        for ycol in self.ycols:
            colattr = next(self.graphColors)

            for rownum, row in enumerate(Progress(self.sourceRows)):  # rows being plotted from source
                try:
                    k = tuple(c.getValue(row) for c in catcols)
                    if k:
                        attr = self.legends.get(k, None)
                        if attr is None:
                            attr = next(self.graphColors)
                            self.plotlegend(len(self.legends), '|'.join(k), attr) # improve loading experience
                            self.legends[k] = attr
                    else:
                        attr = colattr

                    graph_x = float(self.xcols[0].getTypedValue(row)) if self.xcols else rownum
                    graph_y = ycol.getTypedValue(row)

                    self.point(graph_x, graph_y, attr, row)
                    nplotted += 1
                except EscapeException:
                    raise
                except Exception:
                    nerrors += 1
                    if options.debug:
                        raise


        status('loaded %d points (%d errors)' % (nplotted, nerrors))

        self.setZoom(1.0)
        self.refresh()

    def setZoom(self, zoomlevel=None):
        super().setZoom(zoomlevel)
        self.createLabels()

    def add_y_axis_label(self, frac):
        amt = self.visibleGridTop + frac*(self.visibleGridHeight)
        if isinstance(self.gridMinY, int):
            txt = '%d' % amt
        elif isinstance(self.gridMinY, float):
            txt = '%.02f' % amt
        else:
            txt = str(frac)

        # plot y-axis labels on the far left of the canvas, but within the gridCanvas height-wise
        attr = colors[options.color_graph_axis]
        self.plotlabel(0, self.gridCanvasTop + (1.0-frac)*self.gridCanvasHeight, txt, attr)

    def add_x_axis_label(self, frac):
        amt = self.visibleGridLeft + frac*self.visibleGridWidth
        txt = ','.join(xcol.format(xcol.type(amt)) for xcol in self.xcols if isNumeric(xcol))

        # plot x-axis labels below the gridCanvasBottom, but within the gridCanvas width-wise
        attr = colors[options.color_graph_axis]
        self.plotlabel(self.gridCanvasLeft+frac*self.gridCanvasWidth, self.gridCanvasBottom+4, txt, attr)

    def plotAll(self):
        super().plotAll()

    def createLabels(self):
        self.gridlabels = []

        # y-axis
        self.add_y_axis_label(1.00)
        self.add_y_axis_label(0.75)
        self.add_y_axis_label(0.50)
        self.add_y_axis_label(0.25)
        self.add_y_axis_label(0.00)

        # x-axis
        self.add_x_axis_label(1.00)
        self.add_x_axis_label(0.75)
        self.add_x_axis_label(0.50)
        self.add_x_axis_label(0.25)
        self.add_x_axis_label(0.00)

        # TODO: if 0 line is within visibleGrid, explicitly draw on the axis
        # TODO: grid lines corresponding to axis labels

        xname = ','.join(xcol.name for xcol in self.xcols if isNumeric(xcol)) or 'row#'
        self.plotlabel(0, self.gridCanvasBottom+4, '%*s»' % (int(self.leftMarginPixels/2-2), xname), colors[options.color_graph_axis])

        for i, (k, attr) in enumerate(self.legends.items()):
            self.plotlegend(i, '|'.join(k), attr)
