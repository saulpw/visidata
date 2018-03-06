from visidata import *

option('color_graph_axis', 'bold', 'color for graph axis labels')

globalCommand('.', 'vd.push(GraphSheet(sheet.name+"_graph", sheet, selectedRows or rows, keyCols, [cursorCol]))', 'graph the current column vs key columns Numeric key column is on the x-axis, while categorical key columns determin color', 'data-plot-column')
globalCommand('g.', 'vd.push(GraphSheet(sheet.name+"_graph", sheet, selectedRows or rows, keyCols, numericCols(nonKeyVisibleCols)))', 'open a graph of all visible numeric columns vs key column', 'data-plot-allnumeric')


def numericCols(cols):
    # isNumeric from describe.py
    return [c for c in cols if isNumeric(c)]


class InvertedCanvas(Canvas):
    commands = Canvas.commands + [
        # swap directions of up/down
        Command('move-up', 'sheet.cursorBox.ymin += cursorBox.h', 'move cursor up'),
        Command('move-down', 'sheet.cursorBox.ymin -= cursorBox.h', 'move cursor down'),

        Command('zj', 'sheet.cursorBox.ymin -= canvasCharHeight', 'move cursor down one line'),
        Command('zk', 'sheet.cursorBox.ymin += canvasCharHeight', 'move cursor up one line'),

        Command('J', 'sheet.cursorBox.h -= canvasCharHeight', 'decrease cursor height'),
        Command('K', 'sheet.cursorBox.h += canvasCharHeight', 'increase cursor height'),
    ]

    def zoomTo(self, bbox):
        super().zoomTo(bbox)
        self.fixPoint(Point(self.plotviewBox.xmin, self.plotviewBox.ymax), bbox.xymin)

    def plotpixel(self, x, y, attr, row=None):
        y = self.plotviewBox.ymax-y+4
        self.pixels[y][x][attr].append(row)

    def scaleY(self, canvasY):
        'returns plotter y coordinate, with y-axis inverted'
        plotterY = super().scaleY(canvasY)
        return (self.plotviewBox.ymax-plotterY+4)

    def canvasH(self, plotterY):
        return (self.plotviewBox.ymax-plotterY)/self.yScaler

    @property
    def canvasMouse(self):
        p = super().canvasMouse
        p.y = self.visibleBox.ymin + (self.plotviewBox.ymax-self.plotterMouse.y)/self.yScaler
        return p


# provides axis labels, legend
class GraphSheet(InvertedCanvas):
    def __init__(self, name, sheet, rows, xcols, ycols, **kwargs):
        super().__init__(name, sheet, sourceRows=rows, **kwargs)

        self.xcols = xcols
        self.ycols = [ycol for ycol in ycols if isNumeric(ycol)] or error('%s is non-numeric' % '/'.join(yc.name for yc in ycols))

    @async
    def reload(self):
        nerrors = 0
        nplotted = 0

        self.reset()

        status('loading data points')
        catcols = [c for c in self.xcols if not isNumeric(c)]
        numcols = numericCols(self.xcols)
        for ycol in self.ycols:
            for rownum, row in enumerate(Progress(self.sourceRows)):  # rows being plotted from source
                try:
                    k = tuple(c.getValue(row) for c in catcols) if catcols else (ycol.name,)

                    # convert deliberately to float (to e.g. linearize date)
                    graph_x = float(numcols[0].type(numcols[0].getValue(row))) if numcols else rownum
                    graph_y = ycol.type(ycol.getValue(row))

                    attr = self.plotColor(k)
                    self.point(graph_x, graph_y, attr, row)
                    nplotted += 1
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
        amt = self.visibleBox.ymin + frac*self.visibleBox.h
        if isinstance(self.canvasBox.ymin, int):
            txt = '%d' % amt
        elif isinstance(self.canvasBox.ymin, float):
            txt = '%.02f' % amt
        else:
            txt = str(frac)

        # plot y-axis labels on the far left of the canvas, but within the plotview height-wise
        attr = colors[options.color_graph_axis]
        self.plotlabel(0, self.plotviewBox.ymin + (1.0-frac)*self.plotviewBox.h, txt, attr)

    def add_x_axis_label(self, frac):
        amt = self.visibleBox.xmin + frac*self.visibleBox.w
        txt = ','.join(xcol.format(xcol.type(amt)) for xcol in self.xcols if isNumeric(xcol))

        # plot x-axis labels below the plotviewBox.ymax, but within the plotview width-wise
        attr = colors[options.color_graph_axis]
        self.plotlabel(self.plotviewBox.xmin+frac*self.plotviewBox.w, self.plotviewBox.ymax+4, txt, attr)

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

        # TODO: if 0 line is within visible bounds, explicitly draw the axis
        # TODO: grid lines corresponding to axis labels

        xname = ','.join(xcol.name for xcol in self.xcols if isNumeric(xcol)) or 'row#'
        self.plotlabel(0, self.plotviewBox.ymax+4, '%*s»' % (int(self.leftMarginPixels/2-2), xname), colors[options.color_graph_axis])
