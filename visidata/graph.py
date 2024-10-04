import math

from visidata import VisiData, Canvas, Sheet, Progress, BoundingBox, Point, ColumnsSheet
from visidata import vd, asyncthread, dispwidth, colors, clipstr, ColorAttr, update_attr
from visidata.type_date import date
from statistics import median

vd.theme_option('color_graph_axis', 'bold', 'color for graph axis labels')
vd.theme_option('disp_graph_tick_x', '╵', 'character for graph x-axis ticks')
vd.theme_option('color_graph_refline', '', 'color for graph reference value lines')
vd.theme_option('disp_graph_reflines_x_charset', '▏││▕', 'charset to render vertical reference lines on graph')
vd.theme_option('disp_graph_reflines_y_charset', '▔──▁', 'charset to render horizontal reference lines on graph')
vd.theme_option('disp_graph_multiple_reflines_char', '▒', 'char to render multiple parallel reflines')


@VisiData.api
def numericCols(vd, cols):
    return [c for c in cols if vd.isNumeric(c)]


class InvertedCanvas(Canvas):
    @asyncthread
    def render_async(self):
        self.plot_elements(invert_y=True)

    def fixPoint(self, plotterPoint, canvasPoint):
        'adjust visibleBox.xymin so that canvasPoint is plotted at plotterPoint'
        self.visibleBox.xmin = canvasPoint.x - self.canvasW(plotterPoint.x-self.plotviewBox.xmin)
        self.visibleBox.ymin = canvasPoint.y - self.canvasH(self.plotviewBox.ymax-plotterPoint.y)
        self.resetBounds()

    def rowsWithin(self, plotter_bbox):
        return super().rowsWithin(plotter_bbox, invert_y=True)

    def zoomTo(self, bbox):
        super().zoomTo(bbox)
        self.fixPoint(Point(self.plotviewBox.xmin, self.plotviewBox.ymin),
                      Point(bbox.xmin, bbox.ymax))
        self.resetBounds()

    def scaleY(self, canvasY) -> int:
        'returns a plotter y coordinate for a canvas y coordinate, with the y direction inverted'
        return self.plotviewBox.ymax-round((canvasY-self.visibleBox.ymin)*self.yScaler)

    def unscaleY(self, plotterY_inverted):
        'performs the inverse of scaleY, returns a canvas y coordinate'
        return (self.plotviewBox.ymax-plotterY_inverted)/self.yScaler + self.visibleBox.ymin

    @property
    def canvasMouse(self):
        p = super().canvasMouse
        if not p: return None
        p.y = self.unscaleY(self.plotterMouse.y)
        return p

    def calcTopCursorY(self):
        'ymin for the cursor that will align its top with the top edge of the graph'
        return self.visibleBox.ymax - self.cursorBox.h

    def calcBottomCursorY(self):
        # Shift by 1 plotter pixel, like with goTopCursorY for Canvas. But shift in the
        # opposite direction, because the y-coordinate system is inverted.
        'ymin for the cursor that will align its bottom with the bottom edge of the graph'
        return self.visibleBox.ymin - (1/4 * self.canvasCharHeight)

    def startCursor(self):
        res = super().startCursor()
        if not res: return None
        # Since the y coordinates for plotting increase in the opposite
        # direction from Canvas, the cursor has to be shifted.
        self.cursorBox.ymin -= self.canvasCharHeight

# provides axis labels, legend
class GraphSheet(InvertedCanvas):
    def __init__(self, *names, **kwargs):
        self.ylabel_maxw = 0
        super().__init__(*names, **kwargs)

        self.reflines_x = []
        self.reflines_y = []
        self.reflines_char_x = {}    # { x value in character coordinates -> character to use to draw that vertical line }
        self.reflines_char_y = {}    # { y value in character coordinates -> character to use to draw that horizontal line }

        vd.numericCols(self.xcols) or vd.fail('at least one numeric key col necessary for x-axis')
        self.ycols or vd.fail('%s is non-numeric' % '/'.join(yc.name for yc in kwargs.get('ycols')))

    def resetCanvasDimensions(self, windowHeight, windowWidth):
        if self.left_margin < self.ylabel_maxw:
            self.left_margin = self.ylabel_maxw
        super().resetCanvasDimensions(windowHeight, windowWidth)

    @asyncthread
    def reload(self):
        nerrors = 0
        nplotted = 0

        self.reset()
        self.row_order = {}

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
                    self.row_order[self.source.rowid(row)] = rownum
                    nplotted += 1
                except Exception as e:
                    nerrors += 1
                    if vd.options.debug:
                        vd.exceptionCaught(e)


        vd.status('loaded %d points (%d errors)' % (nplotted, nerrors))

        self.xzoomlevel=self.yzoomlevel=1.0
        self.resetBounds()

    def draw(self, scr):
        windowHeight, windowWidth = scr.getmaxyx()
        if self.needsRefresh:
            self.render(windowHeight, windowWidth)

        # required because we use clear_empty_squares=False for draw_pixels()
        self.draw_empty(scr)
        # draw reflines first so pixels draw over them
        self.draw_reflines(scr)
        # use clear_empty_squares to keep reflines
        self.draw_pixels(scr, clear_empty_squares=False)
        self.draw_labels(scr)

    def draw_reflines(self, scr):
        cursorBBox = self.plotterCursorBox
        # draws only on character cells that have reflines, leaves other cells unaffected
        for char_y in range(0, self.plotheight//4):
            has_y_line = char_y in self.reflines_char_y.keys()
            for char_x in range(0, self.plotwidth//2):
                has_x_line = char_x in self.reflines_char_x.keys()
                if has_x_line or has_y_line:
                    cattr = colors.color_refline
                    if has_x_line:
                        ch = self.reflines_char_x[char_x]
                        # where two lines cross, draw the vertical line, not the horizontal one
                    elif has_y_line:
                        ch = self.reflines_char_y[char_y]
                    # draw cursor
                    if cursorBBox.contains(char_x*2, char_y*4) or \
                        cursorBBox.contains(char_x*2+1, char_y*4+3):
                        cattr = update_attr(cattr, colors.color_current_row)
                    scr.addstr(char_y, char_x, ch, cattr.attr)

    def resetBounds(self, refresh=True):
        super().resetBounds(refresh=False)
        self.createLabels()
        if refresh:
            self.refresh()

    def moveToRow(self, rowstr):
        ymin, ymax = map(float, map(self.parseY, rowstr.split()))
        self.cursorBox.ymin = ymin
        self.cursorBox.h = ymax-ymin
        return True

    def plot_elements(self, invert_y=True):
        self.plot_reflines()
        super().plot_elements(invert_y=True)

    def plot_reflines(self):
        self.reflines_char_x = {}
        self.reflines_char_y = {}

        bb = self.visibleBox
        xmin, ymin, xmax, ymax = bb.xmin, bb.ymin, bb.xmax, bb.ymax

        for data_y in self.reflines_y:
            data_y = float(data_y)
            if data_y >= ymin and data_y <= ymax:
                char_y, offset = divmod(self.scaleY(data_y), 4)
                chars = self.options.disp_graph_reflines_y_charset
                # if we're drawing two different reflines in the same square, fill it with a different char
                if char_y in self.reflines_char_y and self.reflines_char_y[char_y] != chars[offset]:
                    self.reflines_char_y[char_y] = vd.options.disp_graph_multiple_reflines_char
                else:
                    self.reflines_char_y[char_y] = chars[offset]

        for data_x in self.reflines_x:
            data_x = float(data_x)
            if data_x >= xmin and data_x <= xmax:
                plot_x = self.scaleX(data_x)
                # plot_x is an integer count of plotter pixels, and each character box has 2 plotter pixels
                char_x = plot_x // 2
                # To subdivide the 2 plotter pixels per square into 4 zones, we have to first multiply by 2.
                offset = 2*plot_x % 4
                chars = self.options.disp_graph_reflines_x_charset
                # if we're drawing two different reflines in the same square, fill it with a different char
                if char_x in self.reflines_char_x and self.reflines_char_x[char_x] != chars[offset]:
                    self.reflines_char_y[char_x] = vd.options.disp_graph_multiple_reflines_char
                else:
                    self.reflines_char_x[char_x] = chars[offset]

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

    def formatXLabel(self, amt):
        if self.xzoomlevel < 1:
            labels = []
            for xcol in self.xcols:
                if vd.isNumeric(xcol):
                    col_amt = float(amt) if xcol.type is int else xcol.type(amt)
                else:
                    continue
                labels.append(xcol.format(col_amt))
            return ','.join(labels)
        else:
            return self.formatX(amt)

    def formatYLabel(self, amt):
        srccol = self.ycols[0]
        if srccol.type is int and self.yzoomlevel < 1:
            return srccol.format(float(amt))
        else:
            return self.formatY(amt)

    def parseX(self, txt):
        return self.xcols[0].type(txt)

    def parseY(self, txt):
        return self.ycols[0].type(txt)

    def add_y_axis_label(self, frac):
        label_data_y = self.visibleBox.ymin + frac*self.visibleBox.h
        txt = self.formatYLabel(label_data_y)
        w = (dispwidth(txt)+1)*2
        if self.ylabel_maxw < w:
            self.ylabel_maxw = w
        y = self.scaleY(label_data_y)

        # plot y-axis labels on the far left of the canvas, but within the plotview height-wise
        self.plotlabel(0, y, txt, 'graph_axis')

    def add_x_axis_label(self, frac):
        label_data_x = self.visibleBox.xmin + frac*self.visibleBox.w
        txt = self.formatXLabel(label_data_x)
        tick = vd.options.disp_graph_tick_x or ''

        # plot x-axis labels below the plotviewBox.ymax, but within the plotview width-wise
        x = self.scaleX(label_data_x)

        if frac < 1.0:
            txt = tick + txt
        else:
            right_margin = self.plotwidth - 1 - self.plotviewBox.xmax
            if (len(txt)+len(tick))*2 <= right_margin:
                txt = tick + txt
            else:
                # shift rightmost label to be left of its tick
                x -= len(txt)*2
                if len(tick) == 0:
                    x += 1
                txt = txt + tick

        self.plotlabel(x, self.plotviewBox.ymax+4, txt, 'graph_axis')

    def createLabels(self):
        self.gridlabels = []
        self.ylabel_maxw = self.leftMarginPixels

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
        xname, _ = clipstr(xname, self.left_margin//2-2)
        self.plotlabel(0, self.plotviewBox.ymax+4, xname+'»', 'graph_axis')

    def rowsWithin(self, plotter_bbox):
        'return list of deduped rows within plotter_bbox'
        rows = super().rowsWithin(plotter_bbox)
        return sorted(rows, key=lambda r: self.row_order[self.source.rowid(r)])

    def draw_refline_x(self):
        xcol = vd.numericCols(self.xcols)[0]
        xtype = xcol.type
        val = median(xcol.getValues(self.sourceRows))
        suggested = format_input_value(val, xtype)
        xstrs = vd.input("add line(s) at x = ", type="reflinex", value=suggested, defaultLast=True).split()

        for xstr in xstrs:
            vals = [ v.strip() for v in xstr.split(',') ]
            if len(vals) != len(self.xcols):
                vd.fail(f'must have {len(self.xcols)} x values, had {len(vals)} values: {xstr}')
            self.reflines_x += [xtype(val) for xcol, val in zip(self.xcols, vals) if xtype(val) not in self.reflines_x ]
        self.refresh()

    def draw_refline_y(self):
        ytype = self.ycols[0].type
        val = median(self.ycols[0].getValues(self.sourceRows))
        suggested = format_input_value(val, ytype)
        ystrs = vd.input("add line(s) at y = ", type="refliney", value=suggested, defaultLast=True).split()

        self.reflines_y += [ ytype(y) for y in ystrs if ytype(y) not in self.reflines_y ]
        self.refresh()

    def erase_refline_x(self):
        if len(self.reflines_x) == 0:
            vd.fail(f'no x refline to erase')
        xtype = vd.numericCols(self.xcols)[0].type
        suggested = format_input_value(self.reflines_x[0], xtype)

        xstrs = vd.input('remove line(s) at x = ', value=suggested, type='reflinex', defaultLast=True).split()
        for input_x in xstrs:
            self.reflines_x.remove(xtype(input_x))
        self.refresh()

    def erase_refline_y(self):
        ytype = self.ycols[0].type
        suggested = format_input_value(self.reflines_y[0], ytype) if self.reflines_y else ''
        ystrs = vd.input('remove line(s) at y = ', value=suggested, type='refliney', defaultLast=True).split()
        for y in ystrs:
            try:
                self.reflines_y.remove(ytype(y))
            except ValueError:
                vd.fail(f'value {y} not in reflines_y')
        self.refresh()

def format_input_value(val, type):
    '''format a value for entry into vd.input(), so its representation has no spaces and no commas'''
    if type is date:
        return val.strftime('%Y-%m-%d')
    else:
        return str(val)


Sheet.addCommand('.', 'plot-column', 'vd.push(GraphSheet(sheet.name, "graph", source=sheet, sourceRows=rows, xcols=keyCols, ycols=numericCols([cursorCol])))', 'plot current numeric column vs key columns; numeric key column is used for x-axis, while categorical key columns determine color')
Sheet.addCommand('g.', 'plot-numerics', 'vd.push(GraphSheet(sheet.name, "graph", source=sheet, sourceRows=rows, xcols=keyCols, ycols=numericCols(nonKeyVisibleCols)))', 'plot a graph of all visible numeric columns vs key columns')
ColumnsSheet.addCommand('g.', 'plot-source-selected', 'vd.push(GraphSheet(sheet.source[0].name, "graph", source=source[0], sourceRows=source[0].rows, xcols=source[0].keyCols, ycols=numericCols(selectedRows)))', 'plot a graph of all selected columns vs key columns on source sheet')

# swap directions of up/down
InvertedCanvas.addCommand(None, 'go-up', 'if cursorBox: sheet.cursorBox.ymin += cursorBox.h', 'move cursor up by its height')
InvertedCanvas.addCommand(None, 'go-down', 'if cursorBox: sheet.cursorBox.ymin -= cursorBox.h', 'move cursor down by its height')
InvertedCanvas.addCommand(None, 'go-top',  'if cursorBox: sheet.cursorBox.ymin = sheet.calcTopCursorY()', 'move cursor to top edge of visible canvas')
InvertedCanvas.addCommand(None, 'go-bottom', 'if cursorBox: sheet.cursorBox.ymin = sheet.calcBottomCursorY()', 'move cursor to bottom edge of visible canvas')
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

GraphSheet.addCommand('gx', 'draw-refline-x', 'sheet.draw_refline_x()', 'draw a vertical line at x-values (space-separated)')
GraphSheet.addCommand('gy', 'draw-refline-y', 'sheet.draw_refline_y()', 'draw a horizontal line at y-values (space-separated)')
GraphSheet.addCommand('zx', 'erase-refline-x', 'sheet.erase_refline_x()', 'remove a horizontal line at x-values (space-separated)')
GraphSheet.addCommand('zy', 'erase-refline-y', 'sheet.erase_refline_y()', 'remove a vertical line at y-values (space-separated)')
GraphSheet.addCommand('gzx', 'erase-reflines-x', 'sheet.reflines_x = []; sheet.refresh()', 'erase all vertical x-value lines')
GraphSheet.addCommand('gzy', 'erase-reflines-y', 'sheet.reflines_y = []; sheet.refresh()', 'erase any horizontal y-value lines')

vd.addGlobals({
    'GraphSheet': GraphSheet,
    'InvertedCanvas': InvertedCanvas,
})

vd.addMenuItems('''
    Plot > Graph > current column > plot-column
    Plot > Graph > all numeric columns > plot-numerics
    Plot > Refline > draw at x coord (vert) > draw-refline-x
    Plot > Refline > draw at y coord (horiz) > draw-refline-y
    Plot > Refline > erase at x coord (vert) > erase-refline-x
    Plot > Refline > erase at y coord (horiz) > erase-refline-y
    Plot > Refline > erase all x (vert) > erase-reflines-x
    Plot > Refline > erase all y (horiz) > erase-reflines-y
''')
