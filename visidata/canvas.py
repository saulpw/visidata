import math
import random

from collections import defaultdict, Counter, OrderedDict
from visidata import vd, asyncthread, ENTER, colors, update_attr, clipdraw, dispwidth
from visidata import BaseSheet, Column, Progress, ColorAttr
from visidata.bezier import bezier

# see www/design/graphics.md

vd.theme_option('disp_graph_labels', True, 'show axes and legend on graph')
vd.theme_option('plot_colors', 'green red yellow cyan magenta white 38 136 168', 'list of distinct colors to use for plotting distinct objects')
vd.theme_option('disp_canvas_charset', ''.join(chr(0x2800+i) for i in range(256)), 'charset to render 2x4 blocks on canvas')
vd.theme_option('disp_pixel_random', False, 'randomly choose attr from set of pixels instead of most common')
vd.theme_option('disp_zoom_incr', 2.0, 'amount to multiply current zoomlevel when zooming')
vd.theme_option('color_graph_hidden', '238 blue', 'color of legend for hidden attribute')
vd.theme_option('color_graph_selected', 'bold', 'color of selected graph points')


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

    def plotpixel(self, x, y, attr:"str|ColorAttr=''", row=None):
        self.pixels[y][x][attr].append(row)

    def plotline(self, x1, y1, x2, y2, attr:"str|ColorAttr=''", row=None):
        for x, y in iterline(x1, y1, x2, y2):
            self.plotpixel(math.ceil(x), math.ceil(y), attr, row)

    def plotlabel(self, x, y, text, attr:"str|ColorAttr=''", row=None):
        self.labels.append((x, y, text, attr, row))

    def plotlegend(self, i, txt, attr:"str|ColorAttr=''", width=15):
        # move it 1 character to the left b/c the rightmost column can't be drawn to
        self.plotlabel(self.plotwidth-(width+1)*2, i*4, txt, attr)

    @property
    def plotterCursorBox(self):
        'Returns pixel bounds of cursor as a Box.  Override to provide a cursor.'
        return Box(0,0,0,0)

    @property
    def plotterMouse(self):
        return Point(*self.plotterFromTerminalCoord(self.mouseX, self.mouseY))

    def plotterFromTerminalCoord(self, x, y):
        return x*2, y*4

    def getPixelAttrRandom(self, x, y) -> str:
        'weighted-random choice of colornum at this pixel.'
        c = list(attr for attr, rows in self.pixels[y][x].items()
                         for r in rows if attr and attr not in self.hiddenAttrs)
        return random.choice(c) if c else 0

    def getPixelAttrMost(self, x, y) -> str:
        'most common colornum at this pixel.'
        r = self.pixels[y][x]
        if not r:
            return 0
        c = [(len(rows), attr, rows) for attr, rows in r.items() if attr and attr not in self.hiddenAttrs]
        if not c:
            return 0
        _, attr, rows = max(c)
        return attr

    def hideAttr(self, attr:str, hide=True):
        if hide:
            self.hiddenAttrs.add(attr)
        else:
            self.hiddenAttrs.remove(attr)
        self.plotlegends()

    def rowsWithin(self, plotter_bbox):
        'return list of deduped rows within plotter_bbox'
        ret = {}
        x_start = max(0, plotter_bbox.xmin)
        y_start = max(0, plotter_bbox.ymin)
        y_end = min(len(self.pixels), plotter_bbox.ymax)
        for y in range(y_start, y_end):
            x_end = min(len(self.pixels[y]), plotter_bbox.xmax)
            for x in range(x_start, x_end):
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
                        color = Counter(c for c in block_attrs if c).most_common(1)[0][0]
                        cattr = colors.get_color(color)
                    else:
                        cattr = ColorAttr()

                    if cursorBBox.contains(char_x*2, char_y*4) or \
                       cursorBBox.contains(char_x*2+1, char_y*4+3):
                        cattr = update_attr(cattr, colors.color_current_row)

                    if cattr.attr:
                        scr.addstr(char_y, char_x, disp_canvas_charset[braille_num], cattr.attr)

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

        if self.options.disp_graph_labels:
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
                        cattr = colors.get_color(attr)
                        clipdraw(scr, char_y, char_x, txt, cattr, dispwidth(txt))
                        cursorBBox = self.plotterCursorBox
                        for c in txt:
                            w = dispwidth(c)
                            # check if the cursor contains the midpoint of the character box
                            if cursorBBox.contains(char_x*2+1, char_y*4+2):
                                char_attr = update_attr(cattr, colors.color_current_row)
                                clipdraw(scr, char_y, char_x, c, char_attr, w)
                            char_x += w


# - has a cursor, of arbitrary position and width/height (not restricted to current zoom)
class Canvas(Plotter):
    'zoomable/scrollable virtual canvas with (x,y) coordinates in arbitrary units'
    rowtype = 'plots'
    leftMarginPixels = 10*2
    rightMarginPixels = 4*2
    topMarginPixels = 0*4
    bottomMarginPixels = 1*4  # reserve bottom line for x axis

    def __init__(self, *names, **kwargs):
        self.left_margin = self.leftMarginPixels
        super().__init__(*names, **kwargs)

        self.canvasBox = None   # bounding box of entire canvas, in canvas units
        self.visibleBox = None  # bounding box of visible canvas, in canvas units
        self.cursorBox = None   # bounding box of cursor, in canvas units

        self.aspectRatio = 0.0
        self.xzoomlevel = 1.0
        self.yzoomlevel = 1.0
        self.needsRefresh = False

        self.polylines = []   # list of ([(canvas_x, canvas_y), ...], fgcolornum, row)
        self.gridlabels = []  # list of (grid_x, grid_y, label, fgcolornum, row)

        self.legends = OrderedDict()   # txt: attr  (visible legends only)
        self.plotAttrs = {}   # key: attr  (all keys, for speed)
        self.reset()

    @property
    def nRows(self):
        return len(self.polylines)

    def reset(self):
        'clear everything in preparation for a fresh reload()'
        self.polylines.clear()
        self.left_margin = self.leftMarginPixels
        self.legends.clear()
        self.legendwidth = 0
        self.plotAttrs.clear()
        self.unusedAttrs = list(self.options.plot_colors.split())

    def plotColor(self, k) -> str:
        attr = self.plotAttrs.get(k, None)
        if attr is None:
            if self.unusedAttrs:
                attr = self.unusedAttrs.pop(0)
                legend = ' '.join(str(x) for x in k)
            else:
                lastlegend, attr = list(self.legends.items())[-1]
                del self.legends[lastlegend]
                legend = '[other]'

            self.legendwidth = max(self.legendwidth, dispwidth(legend))
            self.legends[legend] = attr
            self.plotAttrs[k] = attr
        return attr

    def resetCanvasDimensions(self, windowHeight, windowWidth):
        old_plotsize = None
        realign_cursor = False
        if hasattr(self, 'plotwidth') and hasattr(self, 'plotheight'):
            old_plotsize = [self.plotheight, self.plotwidth]
            if hasattr(self, 'cursorBox') and self.cursorBox and self.visibleBox:
                # if the cursor is at the origin, realign it with the origin after the resize
                if self.cursorBox.xmin == self.visibleBox.xmin and self.cursorBox.ymin == self.calcBottomCursorY():
                    realign_cursor = True
        super().resetCanvasDimensions(windowHeight, windowWidth)
        if hasattr(self, 'legendwidth'):
            # +4 = 1 empty space after the graph + 2 characters for the legend prefixes of "1:", "2:", etc +
            #      1 character for the empty rightmost column
            new_margin = max(self.rightMarginPixels, (self.legendwidth+4)*2)
            pvbox_xmax = self.plotwidth-new_margin-1
            # ensure the graph data takes up at least 3/4 of the width of the screen no matter how wide the legend gets
            pvbox_xmax = max(pvbox_xmax, math.ceil(self.plotwidth * 3/4)//2*2 + 1)
        else:
            pvbox_xmax = self.plotwidth-self.rightMarginPixels-1
        self.left_margin = min(self.left_margin, math.ceil(self.plotwidth * 1/3)//2*2)
        self.plotviewBox = BoundingBox(self.left_margin, self.topMarginPixels,
                                       pvbox_xmax, self.plotheight-self.bottomMarginPixels-1)
        if [self.plotheight, self.plotwidth] != old_plotsize:
            if hasattr(self, 'cursorBox') and self.cursorBox:
                self.setCursorSizeInPlotterPixels(2, 4)
            if realign_cursor:
                self.cursorBox.ymin = self.calcBottomCursorY()

    @property
    def statusLine(self):
        return 'canvas %s visible %s cursor %s' % (self.canvasBox, self.visibleBox, self.cursorBox)

    @property
    def canvasMouse(self):
        x = self.plotterMouse.x
        y = self.plotterMouse.y
        if not self.canvasBox: return None
        p = Point(self.unscaleX(x), self.unscaleY(y))
        return p

    def setCursorSize(self, p):
        'sets width based on diagonal corner p'
        if not p: return
        self.cursorBox = BoundingBox(self.cursorBox.xmin, self.cursorBox.ymin, p.x, p.y)
        self.cursorBox.w = max(self.cursorBox.w, self.canvasCharWidth)
        self.cursorBox.h = max(self.cursorBox.h, self.canvasCharHeight)

    def setCursorSizeInPlotterPixels(self, w, h):
        self.setCursorSize(Point(self.cursorBox.xmin + w/2 * self.canvasCharWidth,
                                 self.cursorBox.ymin + h/4 * self.canvasCharHeight))

    def formatX(self, v):
        return str(v)

    def formatY(self, v):
        return str(v)

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

    def startCursor(self):
        cm = self.canvasMouse
        if cm:
            self.cursorBox = Box(*cm.xy)
            return True
        else:
            return None

    def point(self, x, y, attr:"str|ColorAttr=''", row=None):
        self.polylines.append(([(x, y)], attr, row))

    def line(self, x1, y1, x2, y2, attr:"str|ColorAttr=''", row=None):
        self.polylines.append(([(x1, y1), (x2, y2)], attr, row))

    def polyline(self, vertexes, attr:"str|ColorAttr=''", row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes, attr, row))

    def polygon(self, vertexes, attr:"str|ColorAttr=''", row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes + [vertexes[0]], attr, row))

    def qcurve(self, vertexes, attr:"str|ColorAttr=''", row=None):
        'Draw quadratic curve from vertexes[0] to vertexes[2] with control point at vertexes[1]'
        if len(vertexes) != 3:
            vd.fail('need exactly 3 points for qcurve (got %d)' % len(vertexes))

        x1, y1 = vertexes[0]
        x2, y2 = vertexes[1]
        x3, y3 = vertexes[2]

        for x, y in bezier(x1, y1, x2, y2, x3, y3):
            self.point(x, y, attr, row)

    def label(self, x, y, text, attr:"str|ColorAttr=''", row=None):
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
        'create canvasBox and cursorBox if necessary, and set visibleBox w/h according to zoomlevels.  then redisplay legends.'
        if not self.canvasBox:
            xmin, ymin, xmax, ymax = None, None, None, None
            for vertexes, attr, row in self.polylines:
                for x, y in vertexes:
                    if xmin is None or x < xmin: xmin = x
                    if ymin is None or y < ymin: ymin = y
                    if xmax is None or x > xmax: xmax = x
                    if ymax is None or y > ymax: ymax = y
            xmin = xmin or 0
            xmax = xmax or 0
            ymin = ymin or 0
            ymax = ymax or 0
            if xmin == xmax:
                xmax += 1
            if ymin == ymax:
                ymax += 1
            self.canvasBox = BoundingBox(float(xmin), float(ymin), float(xmax), float(ymax))

        w = self.calcVisibleBoxWidth()
        h = self.calcVisibleBoxHeight()
        if not self.visibleBox:
            # initialize minx/miny, but w/h must be set first to center properly
            self.visibleBox = Box(0, 0, w, h)
            self.visibleBox.xmin = self.canvasBox.xmin + (self.canvasBox.w / 2) * (1 - self.xzoomlevel)
            self.visibleBox.ymin = self.canvasBox.ymin + (self.canvasBox.h / 2) * (1 - self.yzoomlevel)
        else:
            self.visibleBox.w = w
            self.visibleBox.h = h

        if not self.cursorBox:
            cb_xmin = self.visibleBox.xmin
            cb_ymin = self.calcBottomCursorY()
            self.cursorBox = Box(cb_xmin, cb_ymin, self.canvasCharWidth, self.canvasCharHeight)

        self.plotlegends()

    def calcTopCursorY(self):
        'ymin for the cursor that will align its top with the top edge of the graph'
        # + (1/4*self.canvasCharHeight) shifts the cursor up by 1 plotter pixel.
        # That shift makes the cursor contain the top data point.
        # Otherwise, the top data point would have y == plotterCursorBox.ymax,
        # which would not be inside plotterCursorBox. Shifting the cursor makes
        # plotterCursorBox.ymax > y for that top point.
        return self.visibleBox.ymax - self.cursorBox.h + (1/4*self.canvasCharHeight)

    def calcBottomCursorY(self):
        'ymin for the cursor that will align its bottom with the bottom edge of the graph'
        return self.visibleBox.ymin

    def plotlegends(self):
        # display labels
        for i, (legend, attr) in enumerate(self.legends.items()):
            self.addCommand(str(i+1), f'toggle-{i+1}', f'hideAttr("{attr}", "{attr}" not in hiddenAttrs)', f'toggle display of "{legend}"')
            if attr in self.hiddenAttrs:
                attr = 'graph_hidden'
            # add 2 characters to width to account for '1:' '2:' etc
            self.plotlegend(i, '%s:%s'%(i+1,legend), attr, width=self.legendwidth+2)

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

    def calcVisibleBoxWidth(self):
        w = self.canvasBox.w * self.xzoomlevel
        if self.aspectRatio:
            h = self.canvasBox.h * self.yzoomlevel
            xratio = self.plotviewBox.w / w
            yratio = self.plotviewBox.h / h
            if xratio <= yratio:
                return w / self.aspectRatio
            else:
                return self.plotviewBox.w / (self.aspectRatio * yratio)
        else:
            return w

    def calcVisibleBoxHeight(self):
        h = self.canvasBox.h * self.yzoomlevel
        if self.aspectRatio:
            w = self.canvasBox.w * self.yzoomlevel
            xratio = self.plotviewBox.w / w
            yratio = self.plotviewBox.h / h
            if xratio < yratio:
                return self.plotviewBox.h / xratio
            else:
                return h
        else:
            return h

    def scaleX(self, canvasX):
        'returns a plotter x coordinate'
        return round(self.plotviewBox.xmin+(canvasX-self.visibleBox.xmin)*self.xScaler)

    def scaleY(self, canvasY):
        'returns a plotter y coordinate'
        return round(self.plotviewBox.ymin+(canvasY-self.visibleBox.ymin)*self.yScaler)

    def unscaleX(self, plotterX):
        'performs the inverse of scaleX, returns a canvas x coordinate'
        return (plotterX-self.plotviewBox.xmin)/self.xScaler + self.visibleBox.xmin

    def unscaleY(self, plotterY):
        'performs the inverse of scaleY, returns a canvas y coordinate'
        return (plotterY-self.plotviewBox.ymin)/self.yScaler + self.visibleBox.ymin

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
        self.plot_elements()

    def plot_elements(self, invert_y=False):
        'plots points and lines and text onto the plotter'

        self.resetBounds()

        bb = self.visibleBox
        xmin, ymin, xmax, ymax = bb.xmin, bb.ymin, bb.xmax, bb.ymax
        xfactor, yfactor = self.xScaler, self.yScaler
        plotxmin = self.plotviewBox.xmin
        if invert_y:
            plotymax = self.plotviewBox.ymax
        else:
            plotymin = self.plotviewBox.ymin

        for vertexes, attr, row in Progress(self.polylines, 'rendering'):
            if len(vertexes) == 1:  # single point
                x1, y1 = vertexes[0]
                x1, y1 = float(x1), float(y1)
                if xmin <= x1 <= xmax and ymin <= y1 <= ymax:
                    # equivalent to self.scaleX(x1) and self.scaleY(y1), inlined for speed
                    x = plotxmin+(x1-xmin)*xfactor
                    if invert_y:
                        y = plotymax-(y1-ymin)*yfactor
                    else:
                        y = plotymin+(y1-ymin)*yfactor
                    self.plotpixel(round(x), round(y), attr, row)
                continue

            prev_x, prev_y = vertexes[0]
            for x, y in vertexes[1:]:
                r = clipline(prev_x, prev_y, x, y, xmin, ymin, xmax, ymax)
                if r:
                    x1, y1, x2, y2 = r
                    x1 = plotxmin+float(x1-xmin)*xfactor
                    x2 = plotxmin+float(x2-xmin)*xfactor
                    if invert_y:
                        y1 = plotymax-float(y1-ymin)*yfactor
                        y2 = plotymax-float(y2-ymin)*yfactor
                    else:
                        y1 = plotymin+float(y1-ymin)*yfactor
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


Plotter.addCommand('v', 'visibility', 'options.disp_graph_labels = not options.disp_graph_labels', 'toggle disp_graph_labels option')

Canvas.addCommand(None, 'go-left', 'if cursorBox: sheet.cursorBox.xmin -= cursorBox.w', 'move cursor left by its width')
Canvas.addCommand(None, 'go-right', 'if cursorBox: sheet.cursorBox.xmin += cursorBox.w', 'move cursor right by its width' )
Canvas.addCommand(None, 'go-up', 'if cursorBox: sheet.cursorBox.ymin -= cursorBox.h', 'move cursor up by its height')
Canvas.addCommand(None, 'go-down', 'if cursorBox: sheet.cursorBox.ymin += cursorBox.h', 'move cursor down by its height')
Canvas.addCommand(None, 'go-leftmost', 'if cursorBox: sheet.cursorBox.xmin = visibleBox.xmin', 'move cursor to left edge of visible canvas')
Canvas.addCommand(None, 'go-rightmost', 'if cursorBox: sheet.cursorBox.xmin = visibleBox.xmax-cursorBox.w+(1/2*canvasCharWidth)', 'move cursor to right edge of visible canvas')
Canvas.addCommand(None, 'go-top',    'if cursorBox: sheet.cursorBox.ymin = sheet.calcTopCursorY()', 'move cursor to top edge of visible canvas')
Canvas.addCommand(None, 'go-bottom', 'if cursorBox: sheet.cursorBox.ymin = sheet.calcBottomCursorY()', 'move cursor to bottom edge of visible canvas')

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

Canvas.addCommand('-', 'zoomout-cursor', 'tmp=cursorBox.center; incrZoom(options.disp_zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom out from cursor center')
Canvas.addCommand('+', 'zoomin-cursor', 'tmp=cursorBox.center; incrZoom(1.0/options.disp_zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom into cursor center')
Canvas.addCommand('_', 'zoom-all', 'sheet.canvasBox = None; sheet.visibleBox = None; sheet.xzoomlevel=sheet.yzoomlevel=1.0; resetBounds(); refresh()', 'zoom to fit full extent')
Canvas.addCommand('z_', 'set-aspect', 'sheet.aspectRatio = float(input("aspect ratio=", value=aspectRatio)); refresh()', 'set aspect ratio')

# set cursor box with left click
Canvas.addCommand('BUTTON1_PRESSED', 'start-cursor', 'startCursor()', 'start cursor box with left mouse button press')
Canvas.addCommand('BUTTON1_RELEASED', 'end-cursor', 'cm=canvasMouse; setCursorSize(cm) if cm else None', 'end cursor box with left mouse button release')
Canvas.addCommand('BUTTON1_CLICKED', 'remake-cursor', 'startCursor(); cm=canvasMouse; setCursorSize(cm) if cm else None', 'end cursor box with left mouse button release')
Canvas.bindkey('BUTTON1_DOUBLE_CLICKED', 'remake-cursor')
Canvas.bindkey('BUTTON1_TRIPLE_CLICKED', 'remake-cursor')

Canvas.addCommand('BUTTON3_PRESSED', 'start-move', 'cm=canvasMouse; sheet.anchorPoint = cm if cm else None', 'mark grid point to move')
Canvas.addCommand('BUTTON3_RELEASED', 'end-move', 'fixPoint(plotterMouse, anchorPoint) if anchorPoint else None', 'mark canvas anchor point')
# A click does not actually move the canvas, but gives useful UI feedback. It helps users understand that they can do press-drag-release.
Canvas.addCommand('BUTTON3_CLICKED', 'move-canvas',  '', 'move canvas (in place)')
Canvas.bindkey('BUTTON3_DOUBLE_CLICKED', 'move-canvas')
Canvas.bindkey('BUTTON3_TRIPLE_CLICKED', 'move-canvas')

Canvas.addCommand('ScrollUp', 'zoomin-mouse', 'cm=canvasMouse; incrZoom(1.0/options.disp_zoom_incr) if cm else fail("cannot zoom in on unplotted canvas"); fixPoint(plotterMouse, cm)', 'zoom in with scroll wheel')
Canvas.addCommand('ScrollDown', 'zoomout-mouse', 'cm=canvasMouse; incrZoom(options.disp_zoom_incr) if cm else fail("cannot zoom out on unplotted canvas"); fixPoint(plotterMouse, cm)', 'zoom out with scroll wheel')

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

vd.addMenuItems('''
    Plot > Resize cursor > height > double > resize-cursor-doubleheight
    Plot > Resize cursor > height > half > resize-cursor-halfheight
    Plot > Resize cursor > height > shorter > resize-cursor-shorter
    Plot > Resize cursor > height > taller > resize-cursor-taller
    Plot > Resize cursor > width > double > resize-cursor-doublewide
    Plot > Resize cursor > width > half > resize-cursor-halfwide
    Plot > Resize cursor > width > thinner > resize-cursor-thinner
    Plot > Resize cursor > width > wider > resize-cursor-wider
    Plot > Resize graph > X axis > resize-x-input
    Plot > Resize graph > Y axis > resize-y-input
    Plot > Resize graph > aspect ratio > set-aspect
    Plot > Zoom > out > zoomout-cursor
    Plot > Zoom > in > zoomin-cursor
    Plot > Zoom > cursor > zoom-all
    Plot > Dive into cursor > dive-cursor
    Plot > Delete > under cursor > delete-cursor
''')
