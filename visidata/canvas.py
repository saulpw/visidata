
from collections import defaultdict, Counter
from visidata import *

# see www/design/graphics.md

option('show_graph_labels', True, 'show axes and legend on graph')
option('plot_colors', 'green red yellow cyan magenta white 38 136 168', 'list of distinct colors to use for plotting distinct objects')
option('disp_pixel_random', False, 'randomly choose attr from set of pixels instead of most common')
option('zoom_incr', 2.0, 'amount to multiply current zoomlevel when zooming')
option('color_graph_hidden', '238 blue', 'color of legend for hidden attribute')


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
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
    columns=[Column('')]  # to eliminate errors outside of draw()
    rowtype='pixels'
    commands=[
        Command('^L', 'refresh()', 'redraw all pixels on canvas'),
        Command('v', 'options.show_graph_labels = not options.show_graph_labels', 'toggle show_graph_labels'),
        Command('KEY_RESIZE', 'refresh()', ''),
    ]
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.labels = []  # (x, y, text, attr, row)
        self.hiddenAttrs = set()
        self.needsRefresh = False
        self.resetCanvasDimensions()

    def __len__(self):
        return (self.plotwidth* self.plotheight)

    def resetCanvasDimensions(self):
        'sets total available canvas dimensions'
        self.plotwidth = vd().windowWidth*2
        self.plotheight = (vd().windowHeight-1)*4  # exclude status line

        # pixels[y][x] = { attr: list(rows), ... }
        self.pixels = [[defaultdict(list) for x in range(self.plotwidth)] for y in range(self.plotheight)]

    def plotpixel(self, x, y, attr, row=None):
        self.pixels[y][x][attr].append(row)

    def plotline(self, x1, y1, x2, y2, attr, row=None):
        for x, y in iterline(x1, y1, x2, y2):
            self.plotpixel(math.ceil(x), math.ceil(y), attr, row)

    def plotlabel(self, x, y, text, attr, row=None):
        self.labels.append((x, y, text, attr, row))

    def plotlegend(self, i, txt, attr):
        self.plotlabel(self.plotwidth-30, i*4, txt, attr)

    @property
    def plotterCursorBox(self):
        'Returns pixel bounds of cursor as a Box.  Override to provide a cursor.'
        return Box(0,0,0,0)

    @property
    def plotterMouse(self):
        return Point(self.mouseX*2, self.mouseY*4)

    def getPixelAttrRandom(self, x, y):
        'weighted-random choice of attr at this pixel.'
        c = list(attr for attr, rows in self.pixels[y][x].items()
                         for r in rows if attr and attr not in self.hiddenAttrs)
        return random.choice(c) if c else 0

    def getPixelAttrMost(self, x, y):
        'most common attr at this pixel.'
        r = self.pixels[y][x]
        c = sorted((len(rows), attr, rows) for attr, rows in r.items() if attr and attr not in self.hiddenAttrs)
        if not c:
            return 0
        _, attr, rows = c[-1]
        if isinstance(self.source, BaseSheet) and anySelected(self.source, rows):
            attr, _ = colors.update(attr, 8, 'bold', 10)
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
        for y in range(bbox.ymin, bbox.ymax+1):
            for x in range(bbox.xmin, bbox.xmax+1):
                for attr, rows in self.pixels[y][x].items():
                    if attr not in self.hiddenAttrs:
                        for r in rows:
                            ret[id(r)] = r
        return list(ret.values())

    def draw(self, scr):
        if self.needsRefresh:
            self.render()

        scr.erase()

        if self.pixels:
            cursorBBox = self.plotterCursorBox
            getPixelAttr = self.getPixelAttrRandom if options.disp_pixel_random else self.getPixelAttrMost
            for char_y in range(0, vd().windowHeight-1):  # save one line for status
                for char_x in range(0, vd().windowWidth):
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
                        attr, _ = colors.update(attr, 0, options.color_current_row, 10)

                    if attr:
                        scr.addstr(char_y, char_x, chr(0x2800+braille_num), attr)

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

        if options.show_graph_labels:
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
    aspectRatio = 0.0
    leftMarginPixels = 10*2
    rightMarginPixels = 6*2
    topMarginPixels = 0
    bottomMarginPixels = 2*4  # reserve bottom line for x axis

    commands = Plotter.commands + [
        Command('move-left', 'sheet.cursorBox.xmin -= cursorBox.w', ''),
        Command('move-right', 'sheet.cursorBox.xmin += cursorBox.w', ''),
        Command('move-down', 'sheet.cursorBox.ymin += cursorBox.h', ''),
        Command('move-up', 'sheet.cursorBox.ymin -= cursorBox.h', ''),

        Command('zh', 'sheet.cursorBox.xmin -= canvasCharWidth', ''),
        Command('zl', 'sheet.cursorBox.xmin += canvasCharWidth', ''),
        Command('zj', 'sheet.cursorBox.ymin += canvasCharHeight', ''),
        Command('zk', 'sheet.cursorBox.ymin -= canvasCharHeight', ''),

        Command('gH', 'sheet.cursorBox.w /= 2', ''),
        Command('gL', 'sheet.cursorBox.w *= 2', ''),
        Command('gJ', 'sheet.cursorBox.h /= 2', ''),
        Command('gK', 'sheet.cursorBox.h *= 2', ''),

        Command('H', 'sheet.cursorBox.w -= canvasCharWidth', ''),
        Command('L', 'sheet.cursorBox.w += canvasCharWidth', ''),
        Command('J', 'sheet.cursorBox.h += canvasCharHeight', ''),
        Command('K', 'sheet.cursorBox.h -= canvasCharHeight', ''),

        Command('zz', 'zoomTo(cursorBox)', 'set visible bounds to cursor'),

        Command('-', 'tmp=cursorBox.center; setZoom(zoomlevel*options.zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom out from cursor center'),
        Command('+', 'tmp=cursorBox.center; setZoom(zoomlevel/options.zoom_incr); fixPoint(plotviewBox.center, tmp)', 'zoom into cursor center'),
        Command('_', 'sheet.canvasBox = None; sheet.visibleBox = None; setZoom(1.0); refresh()', 'zoom to fit full extent'),
        Command('z_', 'sheet.aspectRatio = float(input("aspect ratio=", value=aspectRatio)); refresh()', 'set aspect ratio'),

        # set cursor box with left click
        Command('BUTTON1_PRESSED', 'sheet.cursorBox = Box(*canvasMouse.xy)', 'start cursor box with left mouse button press'),
        Command('BUTTON1_RELEASED', 'setCursorSize(canvasMouse)', 'end cursor box with left mouse button release'),

        Command('BUTTON3_PRESSED', 'sheet.anchorPoint = canvasMouse', 'mark grid point to move'),
        Command('BUTTON3_RELEASED', 'fixPoint(plotterMouse, anchorPoint)', 'mark canvas anchor point'),

        Command('BUTTON4_PRESSED', 'tmp=canvasMouse; setZoom(zoomlevel/options.zoom_incr); fixPoint(plotterMouse, tmp)', 'zoom in with scroll wheel'),
        Command('REPORT_MOUSE_POSITION', 'tmp=canvasMouse; setZoom(zoomlevel*options.zoom_incr); fixPoint(plotterMouse, tmp)', 'zoom out with scroll wheel'),

        Command('s', 'source.select(list(rowsWithin(plotterCursorBox)))', 'select rows on source sheet contained within canvas cursor'),
        Command('t', 'source.toggle(list(rowsWithin(plotterCursorBox)))', 'toggle selection of rows on source sheet contained within canvas cursor'),
        Command('u', 'source.unselect(list(rowsWithin(plotterCursorBox)))', 'unselect rows on source sheet contained within canvas cursor'),
        Command(ENTER, 'vs=copy(source); vs.rows=list(rowsWithin(plotterCursorBox)); vd.push(vs)', 'open sheet of source rows contained within canvas cursor'),
        Command('d', 'source.delete(list(rowsWithin(plotterCursorBox))); reload()', 'delete rows on source sheet contained within canvas cursor'),


        Command('gs', 'source.select(list(rowsWithin(plotterVisibleBox)))', 'select rows on source sheet visible on screen'),
        Command('gt', 'source.toggle(list(rowsWithin(plotterVisibleBox)))', 'toggle selection of rows on source sheet visible on screen'),
        Command('gu', 'source.unselect(list(rowsWithin(plotterVisibleBox)))', 'unselect rows on source sheet visible on screen'),
        Command('g'+ENTER, 'vs=copy(source); vs.rows=list(rowsWithin(plotterVisibleBox)); vd.push(vs)', 'open sheet of source rows visible on screen'),
        Command('gd', 'source.delete(list(rowsWithin(plotterVisibleBox))); reload()', 'delete rows on source sheet visible on screen'),
    ]

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)

        self.canvasBox = None   # bounding box of entire canvas, in canvas units
        self.visibleBox = None  # bounding box of visible canvas, in canvas units
        self.cursorBox = None   # bounding box of cursor, in canvas units

        self.zoomlevel = 1.0
        self.needsRefresh = False

        self.polylines = []   # list of ([(canvas_x, canvas_y), ...], attr, row)
        self.gridlabels = []  # list of (grid_x, grid_y, label, attr, row)

        self.legends = collections.OrderedDict()   # txt: attr  (visible legends only)
        self.plotAttrs = {}   # key: attr  (all keys, for speed)
        self.reset()

    def __len__(self):
        return len(self.polylines)

    def reset(self):
        'clear everything in preparation for a fresh reload()'
        self.polylines.clear()
        self.legends.clear()
        self.plotAttrs.clear()
        self.unusedAttrs = list(colors[colorname.translate(str.maketrans('_', ' '))] for colorname in options.plot_colors.split())

    def plotColor(self, k):
        attr = self.plotAttrs.get(k, None)
        if attr is None:
            if len(self.unusedAttrs) > 1:
                attr = self.unusedAttrs.pop(0)
                legend = ' '.join(str(x) for x in k)
            else:
                attr = self.unusedAttrs[0]
                legend = '[other]'

            self.legends[legend] = attr
            self.plotAttrs[k] = attr
            self.plotlegends()
        return attr

    def resetCanvasDimensions(self):
        super().resetCanvasDimensions()
        self.plotviewBox = BoundingBox(self.leftMarginPixels, self.topMarginPixels,
                                       self.plotwidth-self.rightMarginPixels, self.plotheight-self.bottomMarginPixels)

    @property
    def statusLine(self):
        return 'canvas %s visible %s cursor %s' % (self.canvasBox, self.visibleBox, self.cursorBox)

    @property
    def canvasMouse(self):
        return Point(self.visibleBox.xmin + (self.plotterMouse.x-self.plotviewBox.xmin)/self.xScaler,
                     self.visibleBox.ymin + (self.plotterMouse.y-self.plotviewBox.ymin)/self.yScaler)

    def setCursorSize(self, p):
        'sets width based on diagonal corner p'
        self.cursorBox = BoundingBox(self.cursorBox.xmin, self.cursorBox.ymin, p.x, p.y)
        self.cursorBox.w = max(self.cursorBox.w, self.canvasCharWidth)
        self.cursorBox.h = max(self.cursorBox.h, self.canvasCharHeight)

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

    def point(self, x, y, attr, row=None):
        self.polylines.append(([(x, y)], attr, row))

    def line(self, x1, y1, x2, y2, attr, row=None):
        self.polylines.append(([(x1, y1), (x2, y2)], attr, row))

    def polyline(self, vertexes, attr, row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes, attr, row))

    def polygon(self, vertexes, attr, row=None):
        'adds lines for (x,y) vertexes of a polygon'
        self.polylines.append((vertexes + [vertexes[0]], attr, row))

    def qcurve(self, vertexes, attr, row=None):
        'quadratic curve from vertexes[0] to vertexes[2] with control point at vertexes[1]'
        assert len(vertexes) == 3, len(vertexes)
        x1, y1 = vertexes[0]
        x2, y2 = vertexes[1]
        x3, y3 = vertexes[2]

        self.point(x1, y1, attr, row)
        self._recursive_bezier(x1, y1, x2, y2, x3, y3, attr, row)
        self.point(x3, y3, attr, row)

    def _recursive_bezier(self, x1, y1, x2, y2, x3, y3, attr, row, level=0):
        'from http://www.antigrain.com/research/adaptive_bezier/'
        m_approximation_scale = 10.0
        m_distance_tolerance = (0.5 / m_approximation_scale) ** 2
        m_angle_tolerance = 1 * 2*math.pi/360  # 15 degrees in rads
        curve_angle_tolerance_epsilon = 0.01
        curve_recursion_limit = 32
        curve_collinearity_epsilon = 1e-30

        if level > curve_recursion_limit:
            return

        # Calculate all the mid-points of the line segments

        x12   = (x1 + x2) / 2
        y12   = (y1 + y2) / 2
        x23   = (x2 + x3) / 2
        y23   = (y2 + y3) / 2
        x123  = (x12 + x23) / 2
        y123  = (y12 + y23) / 2

        dx = x3-x1
        dy = y3-y1
        d = abs(((x2 - x3) * dy - (y2 - y3) * dx))

        if d > curve_collinearity_epsilon:
            # Regular care
            if d*d <= m_distance_tolerance * (dx*dx + dy*dy):
                # If the curvature doesn't exceed the distance_tolerance value, we tend to finish subdivisions.
                if m_angle_tolerance < curve_angle_tolerance_epsilon:
                    self.point(x123, y123, attr, row)
                    return

                # Angle & Cusp Condition
                da = abs(math.atan2(y3 - y2, x3 - x2) - math.atan2(y2 - y1, x2 - x1))
                if da >= math.pi:
                    da = 2*math.pi - da

                if da < m_angle_tolerance:
                    # Finally we can stop the recursion
                    self.point(x123, y123, attr, row)
                    return
        else:
            # Collinear case
            dx = x123 - (x1 + x3) / 2
            dy = y123 - (y1 + y3) / 2
            if dx*dx + dy*dy <= m_distance_tolerance:
                self.point(x123, y123, attr, row)
                return

        # Continue subdivision
        self._recursive_bezier(x1, y1, x12, y12, x123, y123, attr, row, level + 1)
        self._recursive_bezier(x123, y123, x23, y23, x3, y3, attr, row, level + 1)

    def label(self, x, y, text, attr, row=None):
        self.gridlabels.append((x, y, text, attr, row))

    def fixPoint(self, plotterPoint, canvasPoint):
        'adjust visibleBox.xymin so that canvasPoint is plotted at plotterPoint'
        self.visibleBox.xmin = canvasPoint.x - self.canvasW(plotterPoint.x-self.plotviewBox.xmin)
        self.visibleBox.ymin = canvasPoint.y - self.canvasH(plotterPoint.y-self.plotviewBox.ymin)
        self.refresh()

    def zoomTo(self, bbox):
        'set visible area to bbox, maintaining aspectRatio if applicable'
        self.fixPoint(self.plotviewBox.xymin, bbox.xymin)
        self.zoomlevel=max(bbox.w/self.canvasBox.w, bbox.h/self.canvasBox.h)

    def setZoom(self, zoomlevel=None):
        if zoomlevel:
            self.zoomlevel = zoomlevel

        self.resetBounds()
        self.plotlegends()

    def resetBounds(self):
        if not self.canvasBox:
            xmin, ymin, xmax, ymax = None, None, None, None
            for vertexes, attr, row in self.polylines:
                for x, y in vertexes:
                    if xmin is None or x < xmin: xmin = x
                    if ymin is None or y < ymin: ymin = y
                    if xmax is None or x > xmax: xmax = x
                    if ymax is None or y > ymax: ymax = y
            self.canvasBox = BoundingBox(xmin or 0, ymin or 0, xmax or 1, ymax or 1)

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

    def plotlegends(self):
        # display labels
        for i, (legend, attr) in enumerate(self.legends.items()):
            self._commands[str(i+1)] = Command(str(i+1), 'hideAttr(%s, %s not in hiddenAttrs)' % (attr, attr), 'toggle display of "%s"' % legend)
            if attr in self.hiddenAttrs:
                attr = colors[options.color_graph_hidden]
            self.plotlegend(i, '%s:%s'%(i+1,legend), attr)

    def checkCursor(self):
        'override Sheet.checkCursor'
        return False

    @property
    def xScaler(self):
        xratio = self.plotviewBox.w/(self.canvasBox.w*self.zoomlevel)
        if self.aspectRatio:
            yratio = self.plotviewBox.h/(self.canvasBox.h*self.zoomlevel)
            return self.aspectRatio*min(xratio, yratio)
        else:
            return xratio

    @property
    def yScaler(self):
        yratio = self.plotviewBox.h/(self.canvasBox.h*self.zoomlevel)
        if self.aspectRatio:
            xratio = self.plotviewBox.w/(self.canvasBox.w*self.zoomlevel)
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

    def render(self):
        'resets plotter, cancels previous render threads, spawns a new render'
        self.needsRefresh = False
        cancelThread(*(t for t in self.currentThreads if t.name == 'plotAll_async'))
        self.labels.clear()
        self.resetCanvasDimensions()
        self.render_async()

    @async
    def render_async(self):
        'plots points and lines and text onto the Plotter'

        self.setZoom()
        bb = self.visibleBox
        xmin, ymin, xmax, ymax = bb.xmin, bb.ymin, bb.xmax, bb.ymax
        xfactor, yfactor = self.xScaler, self.yScaler
        plotxmin, plotymin = self.plotviewBox.xmin, self.plotviewBox.ymin

        for vertexes, attr, row in Progress(self.polylines):
            if len(vertexes) == 1:  # single point
                x1, y1 = vertexes[0]
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
                    x1 = plotxmin+(x1-xmin)*xfactor
                    y1 = plotymin+(y1-ymin)*yfactor
                    x2 = plotxmin+(x2-xmin)*xfactor
                    y2 = plotymin+(y2-ymin)*yfactor
                    self.plotline(x1, y1, x2, y2, attr, row)
                prev_x, prev_y = x, y

        for x, y, text, attr, row in Progress(self.gridlabels):
            self.plotlabel(self.scaleX(x), self.scaleY(y), text, attr, row)

