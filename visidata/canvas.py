import math
import random

from collections import defaultdict, Counter
from visidata import *
from visidata.bezier import bezier

# see www/design/graphics.md

vd.option('show_graph_labels', True, 'show axes and legend on graph')
vd.option('plot_colors', 'green red yellow cyan magenta white 38 136 168', 'list of distinct colors to use for plotting distinct objects')
vd.option('disp_canvas_charset', ''.join(chr(0x2800+i) for i in range(256)), 'charset to render 2x4 blocks on canvas')
vd.option('disp_pixel_random', False, 'randomly choose attr from set of pixels instead of most common')
vd.option('zoom_incr', 2.0, 'amount to multiply current zoomlevel when zooming')
vd.option('color_graph_hidden', '238 blue', 'color of legend for hidden attribute')
vd.option('color_graph_selected', 'bold', 'color of selected graph points')


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        if isinstance(self.x, int):
            return '(%d,%d)' % (self.x, self.y)
        else:
            return '(%.02f,%.02f)' % (self.x, self.y)

    @property
    def xy(self):
        return (self.x, self.y)

class Box:
    def __init__(self, x, y, w=0, h=0):
        self.xmin = x
        self.ymin = y
        self.w = w
        self.h = h

    def __repr__(self):
        return '[%s+%s,%s+%s]' % (self.xmin, self.w, self.ymin, self.h)

    @property
    def xymin(self):
        return Point(self.xmin, self.ymin)

    @property
    def xmax(self):
        return self.xmin + self.w

    @property
    def ymax(self):
        return self.ymin + self.h

    @property
    def center(self):
        return Point(self.xcenter, self.ycenter)

    @property
    def xcenter(self):
        return self.xmin + self.w/2

    @property
    def ycenter(self):
        return self.ymin + self.h/2

    def contains(self, x, y):
        return x >= self.xmin and \
               x < self.xmax and \
               y >= self.ymin and \
               y < self.ymax

def BoundingBox(x1, y1, x2, y2):
    return Box(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))


def clipline(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    'Liang-Barsky algorithm, returns [xn1,yn1,xn2,yn2] of clipped line within given area, or None'
    dx = x2-x1
    dy = y2-y1
    pq = [
        (-dx, x1-xmin),  # left
        ( dx, xmax-x1),  # right
        (-dy, y1-ymin),  # bottom
        ( dy, ymax-y1),  # top
    ]

    u1, u2 = 0, 1
    for p, q in pq:
        if p < 0:  # from outside to inside
            u1 = max(u1, q/p)
        elif p > 0:  # from inside to outside
            u2 = min(u2, q/p)
        else: #  p == 0:  # parallel to bbox
            if q < 0:  # completely outside bbox
                return None

    if u1 > u2:  # completely outside bbox
        return None

    xn1 = x1 + dx*u1
    yn1 = y1 + dy*u1

    xn2 = x1 + dx*u2
    yn2 = y1 + dy*u2

    return xn1, yn1, xn2, yn2

def iterline(x1, y1, x2, y2):
    'Yields (x, y) coords of line from (x1, y1) to (x2, y2)'
    xdiff = abs(x2-x1)
    ydiff = abs(y2-y1)
    xdir = 1 if x1 <= x2 else -1
    ydir = 1 if y1 <= y2 else -1

    r = math.ceil(max(xdiff, ydiff))
    if r == 0:  # point, not line
        yield x1, y1
    else:
        x, y = math.floor(x1), math.floor(y1)
        i = 0
        while i < r:
            x += xdir * xdiff / r
            y += ydir * ydiff / r

            yield x, y
            i += 1


def anySelected(vs, rows):
    for r in rows:
        if vs.isSelected(r):
            return True

#  - width/height are exactly equal to the number of pixels displayable, and can change at any time.
#  - needs to refresh from source on resize
class Plotter(BaseSheet):
    'pixel-addressable display of entire terminal with (x,y) integer pixel coordinates'
    columns=[Column('_')]  # to eliminate errors outside of draw()
    rowtype='pixels'
    def __init__(self, *names, **kwargs):
        super().__init__(*names, **kwargs)
        self.labels = []  # (x, y, text, attr, row)
        self.hiddenAttrs = set()
        self.needsRefresh = False
        self.resetCanvasDimensions(self.windowHeight, self.windowWidth)

    @property
    def nRows(self):
        return (self.plotwidth* self.plotheight)

    def resetCanvasDimensions(self, windowHeight, windowWidth):
        'sets total available canvas dimensions to (windowHeight, windowWidth) (in char cells)'
        self.plotwidth = windowWidth*2
        self.plotheight = (windowHeight-1)*4  # exclude status line

        # pixels[y][x] = { attr: list(rows), ... }
        self.pixels = [[defaultdict(list) for x in range(self.plotwidth)] for y in range(self.plotheight)]

    def plotpixel(self, x, y, attr=0, row=None):
        self.pixels[y][x][attr].append(row)

    def plotline(self, x1, y1, x2, y2, attr=0, row=None):
        for x, y in iterline(x1, y1, x2, y2):
            self.plotpixel(math.ceil(x), math.ceil(y), attr, row)

    def plotlabel(self, x, y, text, attr=0, row=None):
        self.labels.append((x, y, text, attr, row))

    def plotlegend(self, i, txt, attr=0, width=15):
        self.plotlabel(self.plotwidth-width*2, i*4, txt, attr)

    @property
    def plotterCursorBox(self):
        'Returns pixel bounds of cursor as a Box.  Override to provide a cursor.'
        return Box(0,0,0,0)

    @property
    def plotterMouse(self):
        return Point(*self.plotterFromTerminalCoord(self.mouseX, self.mouseY))

    def plotterFromTerminalCoord(self, x, y):
        return x*2, y*4

    def getPixelAttrRandom(self, x, y):
        'weighted-random choice of attr at this pixel.'
        c = list(attr for attr, rows in self.pixels[y][x].items()
                         for r in rows if attr and attr not in self.hiddenAttrs)
        return random.choice(c) if c else 0

    def getPixelAttrMost(self, x, y):
        'most common attr at this pixel.'
        r = self.pixels[y][x]
        if not r:
            return 0
        c = [(len(rows), attr, rows) for attr, rows in r.items() if attr and attr not in self.hiddenAttrs]
        if not c:
            return 0
        _, attr, rows = max(c)
        if isinstance(self.source, BaseSheet) and anySelected(self.source, rows):
            attr = update_attr(ColorAttr(attr, 0, 8, attr), colors.color_graph_selected, 10).attr
        return attr

    def hideAttr(self, attr, hide=True):
        if hide:
            self.hiddenAttrs.add(attr)
        else:
            self.hiddenAttrs.remove(attr)
        self.plotlegends()

    def rowsWithin(self, bbox):
        'return list of deduped rows within bbox'
        ret = {}
        for y in range(bbox.ymin, min(len(self.pixels), bbox.ymax+1)):
            for x in range(bbox.xmin, min(len(self.pixels[y]), bbox.xmax+1)):
                for attr, rows in self.pixels[y][x].items():
                    if attr not in self.hiddenAttrs:
                        for r in rows:
                            ret[self.source.rowid(r)] = r
        return list(ret.values())

    def draw(self, scr):
        windowHeight, windowWidth = scr.getmaxyx()
        disp_canvas_charset = self.options.disp_canvas_charset or ' o'
        disp_canvas_charset += (256 - len(disp_canvas_charset)) * disp_canvas_charset[-1]

        if self.needsRefresh:
            self.render(windowHeight, windowWidth)

        if self.pixels:
            cursorBBox = self.plotterCursorBox
            getPixelAttr = self.getPixelAttrRandom if self.options.disp_pixel_random else self.getPixelAttrMost

            for char_y in range(0, self.plotheight//4):
                for char_x in range(0, self.plotwidth//2):
                    block_attrs = [
                        getPixelAttr(char_x*2  , char_y*4  ),
                        getPixelAttr(char_x*2  , char_y*4+1),
                        getPixelAttr(char_x*2  , char_y*4+2),
                        getPixelAttr(char_x*2+1, char_y*4  ),
                        getPixelAttr(char_x*2+1, char_y*4+1),
                        getPixelAttr(char_x*2+1, char_y*4+2),
                        getPixelAttr(char_x*2  , char_y*4+3),
                        getPixelAttr(char_x*2+1, char_y*4+3),
                    ]

                    pow2 = 1
                    braille_num = 0
                    for c in block_attrs:
                        if c:
                            braille_num += pow2
                        pow2 *= 2

                    if braille_num != 0:
                        attr = Counter(c for c in block_attrs if c).most_common(1)[0][0]
                    else:
                        attr = 0

                    if cursorBBox.contains(char_x*2, char_y*4) or \
                       cursorBBox.contains(char_x*2+1, char_y*4+3):
                        attr = update_attr(ColorAttr(attr, 0, 0, attr), colors.color_current_row).attr

                    if attr:
                        scr.addstr(char_y, char_x, disp_canvas_charset[braille_num], attr)

        def _mark_overlap_text(labels, textobj):
            def _overlaps(a, b):
                a_x1, _, a_txt, _, _ = a
                b_x1, _, b_txt, _, _ = b
                a_x2 = a_x1 + len(a_txt)
                b_x2 = b_x1 + len(b_txt)
                if a_x1 < b_x1 < a_x2 or a_x1 < b_x2 < a_x2 or \
                   b_x1 < a_x1 < b_x2 or b_x1 < a_x2 < b_x2:
                   return True
                else:
                   return False

            label_fldraw = [textobj, True]
            labels.append(label_fldraw)
            for o in labels:
                if _overlaps(o[0], textobj):
                    o[1] = False
                    label_fldraw[1] = False

        if self.options.show_graph_labels:
            labels_by_line = defaultdict(list) # y -> text labels

            for pix_x, pix_y, txt, attr, row in self.labels:
                if attr in self.hiddenAttrs:
                    continue
                if row is not None:
                    pix_x -= len(txt)/2*2
                char_y = int(pix_y/4)
                char_x = int(pix_x/2)
                o = (char_x, char_y, txt, attr, row)
                _mark_overlap_text(labels_by_line[char_y], o)

            for line in labels_by_line.values():
                for o, fldraw in line:
                    if fldraw:
                        char_x, char_y, txt, attr, row = o
                        clipdraw(scr, char_y, char_x, txt, attr, len(txt))


# - has a cursor, of arbitrary position and width/height (not restricted to current zoom)
class Canvas(Plotter):
    'zoomable/scrollable virtual canvas with (x,y) coordinates in arbitrary units'
    rowtype = 'plots'
    leftMarginPixels = 10*2
    rightMarginPixels = 4*2
    topMarginPixels = 0
    bottomMarginPixels = 1*4  # reserve bottom line for x axis

    def __init__(self, *names, **kwargs):
        super().__init__(*names, **kwargs)

        self.canvasBox = None   # bounding box of entire canvas, in canvas units
        self.visibleBox = None  # bounding box of visible canvas, in canvas units
        self.cursorBox = None   # bounding box of cursor, in canvas units

        self.aspectRatio = 0.0
        self.xzoomlevel = 1.0
        self.yzoomlevel = 1.0
        self.needsRefresh = False

        self.polylines = []   # list of ([(canvas_x, canvas_y), ...], attr, row)
        self.gridlabels = []  # list of (grid_x, grid_y, label, attr, row)

        self.legends = collections.OrderedDict()   # txt: attr  (visible legends only)
        self.plotAttrs = {}   # key: attr  (all keys, for speed)
        self.reset()

    @property
    def nRows(self):
        return len(self.polylines)

    def reset(self):
        'clear everything in preparation for a fresh reload()'
        self.polylines.clear()
        self.legends.clear()
        self.legendwidth = 0
        self.plotAttrs.clear()
        self.unusedAttrs = list(colors[colorname.translate(str.maketrans('_', ' '))] for colorname in self.options.plot_colors.split())

    def plotColor(self, k):
        attr = self.plotAttrs.get(k, None)
        if attr is None:
            if self.unusedAttrs:
                attr = self.unusedAttrs.pop(0)
                legend = ' '.join(str(x) for x in k)
            else:
                lastlegend, attr = list(self.legends.items())[-1]
                del self.legends[lastlegend]
                legend = '[other]'

            self.legendwidth = max(self.legendwidth, len(legend))
            self.legends[legend] = attr
            self.plotAttrs[k] = attr
            self.plotlegends()
        return attr

    def resetCanvasDimensions(self, windowHeight, windowWidth):
        super().resetCanvasDimensions(windowHeight, windowWidth)
        self.plotviewBox = BoundingBox(self.leftMarginPixels, self.topMarginPixels,
                                       self.plotwidth-self.rightMarginPixels, self.plotheight-self.bottomMarginPixels-1)

    @property
    def statusLine(self):
        return 'canvas %s visible %s cursor %s' % (self.canvasBox, self.visibleBox, self.cursorBox)

    @property
    def canvasMouse(self):
        return self.canvasFromPlotterCoord(self.plotterMouse.x, self.plotterMouse.y)

    def canvasFromPlotterCoord(self, plotter_x, plotter_y):
        return Point(self.visibleBox.xmin + (plotter_x-self.plotviewBox.xmin)/self.xScaler, self.visibleBox.ymin + (plotter_y-self.plotviewBox.ymin)/self.yScaler)

    def canvasFromTerminalCoord(self, x, y):
        return self.canvasFromPlotterCoord(*self.plotterFromTerminalCoord(x, y))

    def setCursorSize(self, p):
        'sets width based on diagonal corner p'
        self.cursorBox = BoundingBox(self.cursorBox.xmin, self.cursorBox.ymin, p.x, p.y)
        self.cursorBox.w = max(self.cursorBox.w, self.canvasCharWidth)
        self.cursorBox.h = max(self.cursorBox.h, self.canvasCharHeight)

    def commandCursor(sheet, execstr):
        'Return (col, row) of cursor suitable for cmdlog replay of execstr.'
        contains = lambda s, *substrs: any((a in s) for a in substrs)
        colname, rowname = '', ''
        if contains(execstr, 'plotterCursorBox'):
            bb = sheet.cursorBox
            colname = '%s %s' % (sheet.formatX(bb.xmin), sheet.formatX(bb.xmax))
            rowname = '%s %s' % (sheet.formatY(bb.ymin), sheet.formatY(bb.ymax))
        elif contains(execstr, 'plotterVisibleBox'):
            bb = sheet.visibleBox
            colname = '%s %s' % (sheet.formatX(bb.xmin), sheet.formatX(bb.xmax))
            rowname = '%s %s' % (sheet.formatY(bb.ymin), sheet.formatY(bb.ymax))
        return colname, rowname

    @property
    def canvasCharWidth(self):
        'Width in canvas units of a single char in the terminal'
        return self.visibleBox.w*2/self.plotviewBox.w

    @property
    def canvasCharHeight(self):
        'Height in canvas units of a single char in the terminal'
        return self.visibleBox.h*4/self.plotviewBox.h

    @property
    def plotterVisibleBox(self):
        return BoundingBox(self.scaleX(self.visibleBox.xmin),
                           self.scaleY(self.visibleBox.ymin),
                           self.scaleX(self.visibleBox.xmax),
                           self.scaleY(self.visibleBox.ymax))

    @property
    def plotterCursorBox(self):
        if self.cursorBox is None:
            return Box(0,0,0,0)
        return BoundingBox(self.scaleX(self.cursorBox.xmin),
                           self.scaleY(self.cursorBox.ymin),
                           self.scaleX(self.cursorBox.xmax),
                           self.scaleY(self.cursorBox.ymax))

    def point(self, x, y, attr=0, row=None):
        self.polylines.append(([(x, y)], attr, row))

    def line(self, x1, y1, x2, y2, attr=0, row=None):
        self.polylines.append(([(x1, y1), (x2, y2)], attr, row))

    def polyline(self, vertexes, attr=0, row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes, attr, row))

    def polygon(self, vertexes, attr=0, row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes + [vertexes[0]], attr, row))

    def qcurve(self, vertexes, attr=0, row=None):
        'Draw quadratic curve from vertexes[0] to vertexes[2] with control point at vertexes[1]'
        if len(vertexes) != 3:
            vd.fail('need exactly 3 points for qcurve (got %d)' % len(vertexes))

        x1, y1 = vertexes[0]
        x2, y2 = vertexes[1]
        x3, y3 = vertexes[2]

        for x, y in bezier(x1, y1, x2, y2, x3, y3):
            self.point(x, y, attr, row)

    def label(self, x, y, text, attr=0, row=None):
        self.gridlabels.append((x, y, text, attr, row))

    def fixPoint(self, plotterPoint, canvasPoint):
        'adjust visibleBox.xymin so that canvasPoint is plotted at plotterPoint'
        self.visibleBox.xmin = canvasPoint.x - self.canvasW(plotterPoint.x-self.plotviewBox.xmin)
        self.visibleBox.ymin = canvasPoint.y - self.canvasH(plotterPoint.y-self.plotviewBox.ymin)
        self.refresh()

    def zoomTo(self, bbox):
        'set visible area to bbox, maintaining aspectRatio if applicable'
        self.fixPoint(self.plotviewBox.xymin, bbox.xymin)
        self.xzoomlevel=bbox.w/self.canvasBox.w
        self.yzoomlevel=bbox.h/self.canvasBox.h

    def incrZoom(self, incr):
        self.xzoomlevel *= incr
        self.yzoomlevel *= incr

        self.resetBounds()

    def resetBounds(self):
        'create canvasBox and cursorBox if necessary, and set visibleBox w/h according to zoomlevels.  then redisplay labels.'
        if not self.canvasBox:
            xmin, ymin, xmax, ymax = None, None, None, None
            for vertexes, attr, row in self.polylines:
                for x, y in vertexes:
                    if xmin is None or x < xmin: xmin = x
                    if ymin is None or y < ymin: ymin = y
                    if xmax is None or x > xmax: xmax = x
                    if ymax is None or y > ymax: ymax = y
            self.canvasBox = BoundingBox(float(xmin or 0), float(ymin or 0), float(xmax or 1), float(ymax or 1))

        if not self.visibleBox:
            # initialize minx/miny, but w/h must be set first to center properly
            self.visibleBox = Box(0, 0, self.plotviewBox.w/self.xScaler, self.plotviewBox.h/self.yScaler)
            self.visibleBox.xmin = self.canvasBox.xcenter - self.visibleBox.w/2
            self.visibleBox.ymin = self.canvasBox.ycenter - self.visibleBox.h/2
        else:
            self.visibleBox.w = self.plotviewBox.w/self.xScaler
            self.visibleBox.h = self.plotviewBox.h/self.yScaler

        if not self.cursorBox:
            self.cursorBox = Box(self.visibleBox.xmin, self.visibleBox.ymin, self.canvasCharWidth, self.canvasCharHeight)

        self.plotlegends()

    def plotlegends(self):
        # display labels
        for i, (legend, attr) in enumerate(self.legends.items()):
            self.addCommand(str(i+1), 'toggle-%s'%(i+1), 'hideAttr(%s, %s not in hiddenAttrs)' % (attr, attr), 'toggle display of "%s"' % legend)
            if attr in self.hiddenAttrs:
                attr = colors.color_graph_hidden
            self.plotlegend(i, '%s:%s'%(i+1,legend), attr, width=self.legendwidth+4)

    def checkCursor(self):
        'override Sheet.checkCursor'
        if self.visibleBox and self.cursorBox:
            if self.cursorBox.h < self.canvasCharHeight:
                self.cursorBox.h = self.canvasCharHeight*3/4
            if self.cursorBox.w < self.canvasCharWidth:
                self.cursorBox.w = self.canvasCharWidth*3/4

        return False

    @property
    def xScaler(self):
        xratio = self.plotviewBox.w/(self.canvasBox.w*self.xzoomlevel)
        if self.aspectRatio:
            yratio = self.plotviewBox.h/(self.canvasBox.h*self.yzoomlevel)
            return self.aspectRatio*min(xratio, yratio)
        else:
            return xratio

    @property
    def yScaler(self):
        yratio = self.plotviewBox.h/(self.canvasBox.h*self.yzoomlevel)
        if self.aspectRatio:
            xratio = self.plotviewBox.w/(self.canvasBox.w*self.xzoomlevel)
            return min(xratio, yratio)
        else:
            return yratio

    def scaleX(self, x):
        'returns plotter x coordinate'
        return round(self.plotviewBox.xmin+(x-self.visibleBox.xmin)*self.xScaler)

    def scaleY(self, y):
        'returns plotter y coordinate'
        return round(self.plotviewBox.ymin+(y-self.visibleBox.ymin)*self.yScaler)

    def canvasW(self, plotter_width):
        'plotter X units to canvas units'
        return plotter_width/self.xScaler

    def canvasH(self, plotter_height):
        'plotter Y units to canvas units'
        return plotter_height/self.yScaler

    def refresh(self):
        'triggers render() on next draw()'
        self.needsRefresh = True

    def render(self, h, w):
        'resets plotter, cancels previous render threads, spawns a new render'
        self.needsRefresh = False
        vd.cancelThread(*(t for t in self.currentThreads if t.name == 'plotAll_async'))
        self.labels.clear()
        self.resetCanvasDimensions(h, w)
        self.render_async()

    @asyncthread
    def render_async(self):
        self.render_sync()

    def render_sync(self):
        'plots points and lines and text onto the Plotter'

        self.resetBounds()

        bb = self.visibleBox
        xmin, ymin, xmax, ymax = bb.xmin, bb.ymin, bb.xmax, bb.ymax
        xfactor, yfactor = self.xScaler, self.yScaler
        plotxmin, plotymin = self.plotviewBox.xmin, self.plotviewBox.ymin

        for vertexes, attr, row in Progress(self.polylines, 'rendering'):
            if len(vertexes) == 1:  # single point
                x1, y1 = vertexes[0]
                x1, y1 = float(x1), float(y1)
                if xmin <= x1 <= xmax and ymin <= y1 <= ymax:
                    x = plotxmin+(x1-xmin)*xfactor
                    y = plotymin+(y1-ymin)*yfactor
                    self.plotpixel(round(x), round(y), attr, row)
                continue

            prev_x, prev_y = vertexes[0]
            for x, y in vertexes[1:]:
                r = clipline(prev_x, prev_y, x, y, xmin, ymin, xmax, ymax)
                if r:
                    x1, y1, x2, y2 = r
                    x1 = plotxmin+float(x1-xmin)*xfactor
                    y1 = plotymin+float(y1-ymin)*yfactor
                    x2 = plotxmin+float(x2-xmin)*xfactor
                    y2 = plotymin+float(y2-ymin)*yfactor
                    self.plotline(x1, y1, x2, y2, attr, row)
                prev_x, prev_y = x, y

        for x, y, text, attr, row in Progress(self.gridlabels, 'labeling'):
            self.plotlabel(self.scaleX(x), self.scaleY(y), text, attr, row)

    @asyncthread
    def deleteSourceRows(self, rows):
        rows = list(rows)
        self.source.copyRows(rows)
        self.source.deleteBy(lambda r,rows=rows: r in rows)
        self.reload()


Plotter.addCommand('v', 'visibility', 'options.show_graph_labels = not options.show_graph_labels', 'toggle show_graph_labels option')

Canvas.addCommand(None, 'go-left', 'sheet.cursorBox.xmin -= cursorBox.w', 'move cursor left by its width')
Canvas.addCommand(None, 'go-right', 'sheet.cursorBox.xmin += cursorBox.w', 'move cursor right by its width' )
Canvas.addCommand(None, 'go-up', 'sheet.cursorBox.ymin -= cursorBox.h', 'move cursor up by its height')
Canvas.addCommand(None, 'go-down', 'sheet.cursorBox.ymin += cursorBox.h', 'move cursor down by its height')
Canvas.addCommand(None, 'go-leftmost', 'sheet.cursorBox.xmin = visibleBox.xmin', 'move cursor to left edge of visible canvas')
Canvas.addCommand(None, 'go-rightmost', 'sheet.cursorBox.xmin = visibleBox.xmax-cursorBox.w', 'move cursor to right edge of visible canvas')
Canvas.addCommand(None, 'go-top', 'sheet.cursorBox.ymin = visibleBox.ymin', 'move cursor to top edge of visible canvas')
Canvas.addCommand(None, 'go-bottom', 'sheet.cursorBox.ymin = visibleBox.ymax', 'move cursor to bottom edge of visible canvas')

Canvas.addCommand(None, 'go-pagedown', 't=(visibleBox.ymax-visibleBox.ymin); sheet.cursorBox.ymin += t; sheet.visibleBox.ymin += t; refresh()', 'move cursor down to next visible page')
Canvas.addCommand(None, 'go-pageup', 't=(visibleBox.ymax-visibleBox.ymin); sheet.cursorBox.ymin -= t; sheet.visibleBox.ymin -= t; refresh()', 'move cursor up to previous visible page')

Canvas.addCommand('zh', 'go-left-small', 'sheet.cursorBox.xmin -= canvasCharWidth', 'move cursor left one character')
Canvas.addCommand('zl', 'go-right-small', 'sheet.cursorBox.xmin += canvasCharWidth', 'move cursor right one character')
Canvas.addCommand('zj', 'go-down-small', 'sheet.cursorBox.ymin += canvasCharHeight', 'move cursor down one character')
Canvas.addCommand('zk', 'go-up-small', 'sheet.cursorBox.ymin -= canvasCharHeight', 'move cursor up one character')

Canvas.addCommand('gH', 'resize-cursor-halfwide', 'sheet.cursorBox.w /= 2', 'halve cursor width')
Canvas.addCommand('gL', 'resize-cursor-doublewide', 'sheet.cursorBox.w *= 2', 'double cursor width')
Canvas.addCommand('gJ','resize-cursor-halfheight', 'sheet.cursorBox.h /= 2', 'halve cursor height')
Canvas.addCommand('gK', 'resize-cursor-doubleheight', 'sheet.cursorBox.h *= 2', 'double cursor height')

Canvas.addCommand('H', 'resize-cursor-thinner', 'sheet.cursorBox.w -= canvasCharWidth', 'decrease cursor width by one character')
Canvas.addCommand('L', 'resize-cursor-wider', 'sheet.cursorBox.w += canvasCharWidth', 'increase cursor width by one character')
Canvas.addCommand('J', 'resize-cursor-taller', 'sheet.cursorBox.h += canvasCharHeight', 'increase cursor height by one character')
Canvas.addCommand('K', 'resize-cursor-shorter', 'sheet.cursorBox.h -= canvasCharHeight', 'decrease cursor height by one character')
Canvas.addCommand('zz', 'zoom-cursor', 'zoomTo(cursorBox)', 'set visible bounds to cursor')

Canvas.addCommand('-', 'zoomout-cursor', 'tmp=cursorBox.center; incrZoom(options.zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom out from cursor center')
Canvas.addCommand('+', 'zoomin-cursor', 'tmp=cursorBox.center; incrZoom(1.0/options.zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom into cursor center')
Canvas.addCommand('_', 'zoom-all', 'sheet.canvasBox = None; sheet.visibleBox = None; sheet.xzoomlevel=sheet.yzoomlevel=1.0; refresh()', 'zoom to fit full extent')
Canvas.addCommand('z_', 'set-aspect', 'sheet.aspectRatio = float(input("aspect ratio=", value=aspectRatio)); refresh()', 'set aspect ratio')

# set cursor box with left click
Canvas.addCommand('BUTTON1_PRESSED', 'start-cursor', 'sheet.cursorBox = Box(*canvasMouse.xy)', 'start cursor box with left mouse button press')
Canvas.addCommand('BUTTON1_RELEASED', 'end-cursor', 'setCursorSize(canvasMouse)', 'end cursor box with left mouse button release')

Canvas.addCommand('BUTTON3_PRESSED', 'start-move', 'sheet.anchorPoint = canvasMouse', 'mark grid point to move')
Canvas.addCommand('BUTTON3_RELEASED', 'end-move', 'fixPoint(plotterMouse, anchorPoint)', 'mark canvas anchor point')

Canvas.addCommand('BUTTON4_PRESSED', 'zoomin-mouse', 'tmp=canvasMouse; incrZoom(1.0/options.zoom_incr); fixPoint(plotterMouse, tmp)', 'zoom in with scroll wheel')
Canvas.addCommand('REPORT_MOUSE_POSITION', 'zoomout-mouse', 'tmp=canvasMouse; incrZoom(options.zoom_incr); fixPoint(plotterMouse, tmp)', 'zoom out with scroll wheel')
Canvas.bindkey('2097152', 'zoomout-mouse')

Canvas.addCommand('s', 'select-cursor', 'source.select(list(rowsWithin(plotterCursorBox)))', 'select rows on source sheet contained within canvas cursor')
Canvas.addCommand('t', 'stoggle-cursor', 'source.toggle(list(rowsWithin(plotterCursorBox)))', 'toggle selection of rows on source sheet contained within canvas cursor')
Canvas.addCommand('u', 'unselect-cursor', 'source.unselect(list(rowsWithin(plotterCursorBox)))', 'unselect rows on source sheet contained within canvas cursor')
Canvas.addCommand(ENTER, 'dive-cursor', 'vs=copy(source); vs.rows=list(rowsWithin(plotterCursorBox)); vd.push(vs)', 'open sheet of source rows contained within canvas cursor')
Canvas.addCommand('d', 'delete-cursor', 'deleteSourceRows(rowsWithin(plotterCursorBox))', 'delete rows on source sheet contained within canvas cursor')

Canvas.addCommand('gs', 'select-visible', 'source.select(list(rowsWithin(plotterVisibleBox)))', 'select rows on source sheet visible on screen')
Canvas.addCommand('gt', 'stoggle-visible', 'source.toggle(list(rowsWithin(plotterVisibleBox)))', 'toggle selection of rows on source sheet visible on screen')
Canvas.addCommand('gu', 'unselect-visible', 'source.unselect(list(rowsWithin(plotterVisibleBox)))', 'unselect rows on source sheet visible on screen')
Canvas.addCommand('g'+ENTER, 'dive-visible', 'vs=copy(source); vs.rows=list(rowsWithin(plotterVisibleBox)); vd.push(vs)', 'open sheet of source rows visible on screen')
Canvas.addCommand('gd', 'delete-visible', 'deleteSourceRows(rowsWithin(plotterVisibleBox))', 'delete rows on source sheet visible on screen')


vd.addGlobals({
    'Canvas': Canvas,
    'Plotter': Plotter,
    'BoundingBox': BoundingBox,
    'Box': Box,
    'Point': Point,
})
