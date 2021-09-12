from visidata import *

vd.option('color_graph_axis', 'bold', 'color for graph axis labels')


@VisiData.api
def numericCols(vd, cols):
    return [c for c in cols if vd.isNumeric(c)]


class InvertedCanvas(Canvas):
    def zoomTo(self, bbox):
        super().zoomTo(bbox)
        self.fixPoint(Point(self.plotviewBox.xmin, self.plotviewBox.ymax), bbox.xymin)

    def plotpixel(self, x, y, attr, row=None):
        y = self.plotviewBox.ymax-y
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
    def __init__(self, *names, **kwargs):
        super().__init__(*names, **kwargs)

        self.xcols or vd.fail('at least one key col necessary for x-axis')
        self.ycols or vd.fail('%s is non-numeric' % '/'.join(yc.name for yc in kwargs.get('ycols')))

    @asyncthread
    def reload(self):
        nerrors = 0
        nplotted = 0

        self.reset()

        vd.status('loading data points')
        catcols = [c for c in self.xcols if not vd.isNumeric(c)]
        numcols = vd.numericCols(self.xcols)
        for ycol in self.ycols:
            for rownum, row in enumerate(Progress(self.sourceRows, 'plotting')):  # rows being plotted from source
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


        vd.status('loaded %d points (%d errors)' % (nplotted, nerrors))

        self.xzoomlevel=self.yzoomlevel=1.0
        self.resetBounds()
        self.refresh()

    def resetBounds(self):
        super().resetBounds()
        self.createLabels()

    def moveToRow(self, rowstr):
        ymin, ymax = map(float, map(self.parseY, rowstr.split()))
        self.cursorBox.ymin = ymin
        self.cursorBox.h = ymax-ymin
        return True

    def moveToCol(self, colstr):
        xmin, xmax = map(float, map(self.parseX, colstr.split()))
        self.cursorBox.xmin = xmin
        self.cursorBox.w = xmax-xmin
        return True

    def formatX(self, amt):
        return ','.join(xcol.format(xcol.type(amt)) for xcol in self.xcols if vd.isNumeric(xcol))

    def formatY(self, amt):
        srccol = self.ycols[0]
        return srccol.format(srccol.type(amt))

    def parseX(self, txt):
        return self.xcols[0].type(txt)

    def parseY(self, txt):
        return self.ycols[0].type(txt)

    def add_y_axis_label(self, frac):
        txt = self.formatY(self.visibleBox.ymin + frac*self.visibleBox.h)

        # plot y-axis labels on the far left of the canvas, but within the plotview height-wise
        attr = colors.color_graph_axis
        self.plotlabel(0, self.plotviewBox.ymin + (1.0-frac)*self.plotviewBox.h, txt, attr)

    def add_x_axis_label(self, frac):
        txt = self.formatX(self.visibleBox.xmin + frac*self.visibleBox.w)

        # plot x-axis labels below the plotviewBox.ymax, but within the plotview width-wise
        attr = colors.color_graph_axis
        xmin = self.plotviewBox.xmin + frac*self.plotviewBox.w
        if frac == 1.0:
            # shift rightmost label to be readable
            xmin -= max(len(txt)*2 - self.rightMarginPixels+1, 0)

        self.plotlabel(xmin, self.plotviewBox.ymax+4, txt, attr)

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

        xname = ','.join(xcol.name for xcol in self.xcols if vd.isNumeric(xcol)) or 'row#'
        xname, _ = clipstr(xname, self.leftMarginPixels//2-2)
        self.plotlabel(0, self.plotviewBox.ymax+4, xname+'»', colors.color_graph_axis)


Sheet.addCommand('.', 'plot-column', 'vd.push(GraphSheet(sheet.name, "graph", source=sheet, sourceRows=rows, xcols=keyCols, ycols=numericCols([cursorCol])))', 'plot current numeric column vs key columns; numeric key column is used for x-axis, while categorical key columns determine color')
Sheet.addCommand('g.', 'plot-numerics', 'vd.push(GraphSheet(sheet.name, "graph", source=sheet, sourceRows=rows, xcols=keyCols, ycols=numericCols(nonKeyVisibleCols)))', 'plot a graph of all visible numeric columns vs key columns')

# swap directions of up/down
InvertedCanvas.addCommand(None, 'go-up', 'sheet.cursorBox.ymin += cursorBox.h', 'move cursor up by its height')
InvertedCanvas.addCommand(None, 'go-down', 'sheet.cursorBox.ymin -= cursorBox.h', 'move cursor down by its height')
InvertedCanvas.addCommand(None, 'go-top', 'sheet.cursorBox.ymin = visibleBox.ymax', 'move cursor to top edge of visible canvas')
InvertedCanvas.addCommand(None, 'go-bottom', 'sheet.cursorBox.ymin = visibleBox.ymin', 'move cursor to bottom edge of visible canvas')
InvertedCanvas.addCommand(None, 'go-pagedown', 't=(visibleBox.ymax-visibleBox.ymin); sheet.cursorBox.ymin -= t; sheet.visibleBox.ymin -= t; sheet.refresh()', 'move cursor down to next visible page')
InvertedCanvas.addCommand(None, 'go-pageup', 't=(visibleBox.ymax-visibleBox.ymin); sheet.cursorBox.ymin += t; sheet.visibleBox.ymin += t; sheet.refresh()', 'move cursor up to previous visible page')

InvertedCanvas.addCommand(None, 'go-down-small', 'sheet.cursorBox.ymin -= canvasCharHeight', 'move cursor down one character')
InvertedCanvas.addCommand(None, 'go-up-small', 'sheet.cursorBox.ymin += canvasCharHeight', 'move cursor up one character')

InvertedCanvas.addCommand(None, 'resize-cursor-shorter', 'sheet.cursorBox.h -= canvasCharHeight', 'decrease cursor height by one character')
InvertedCanvas.addCommand(None, 'resize-cursor-taller', 'sheet.cursorBox.h += canvasCharHeight', 'increase cursor height by one character')


@GraphSheet.api
def set_y(sheet, s):
    ymin, ymax = map(float, map(sheet.parseY, s.split()))
    sheet.zoomTo(BoundingBox(sheet.visibleBox.xmin, ymin, sheet.visibleBox.xmax, ymax))
    sheet.refresh()

@GraphSheet.api
def set_x(sheet, s):
    xmin, xmax = map(float, map(sheet.parseX, s.split()))
    sheet.zoomTo(BoundingBox(xmin, sheet.visibleBox.ymin, xmax, sheet.visibleBox.ymax))
    sheet.refresh()

Canvas.addCommand('y', 'resize-y-input', 'sheet.set_y(input("set ymin ymax="))', 'set ymin/ymax on graph axes')
Canvas.addCommand('x', 'resize-x-input', 'sheet.set_x(input("set xmin xmax="))', 'set xmin/xmax on graph axes')


vd.addGlobals({
    'GraphSheet': GraphSheet,
    'InvertedCanvas': InvertedCanvas,
})
