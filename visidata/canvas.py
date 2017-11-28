
from collections import defaultdict, Counter
from visidata import *

# see www/design/graphics.md

option('show_graph_labels', True, 'show axes and legend on graph')
option('plot_colors', 'green red yellow cyan magenta white 38 136 168', 'list of distinct colors to use for plotting distinct objects')
option('disp_pixel_random', False, 'randomly choose attr from set of pixels instead of most common')
option('zoom_incr', 2.0, 'amount to multiply current zoomlevel by when zooming')

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
    def xmax(self):
        return self.xmin + self.w

    @property
    def ymax(self):
        return self.ymin + self.h

    @property
    def xcenter(self):
        return self.xmin + self.w/2

    @property
    def ycenter(self):
        return self.ymin + self.h/2

    def within(self, x, y):
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

    r = max(xdiff, ydiff)
    if r == 0:  # point, not line
        yield x1, y1
    else:
        x, y = x1, y1
        i = 0
        while i <= r:
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
class Plotter(Sheet):
    'pixel-addressable display of entire terminal with (x,y) integer pixel coordinates'
    columns=[Column('')]  # to eliminate errors outside of draw()
    commands=[
        Command('^L', 'refresh()', 'redraw all pixels on canvas'),
        Command('w', 'options.show_graph_labels = not options.show_graph_labels', 'toggle show_graph_labels'),
        Command('KEY_RESIZE', 'refresh()', ''),
    ]
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.labels = []  # (x, y, text, attr)
        self.disabledAttrs = set()
        self.needsRefresh = False
        self.resetCanvasDimensions()

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
            self.plotpixel(round(x), round(y), attr, row)

    def plotlabel(self, x, y, text, attr):
        self.labels.append((x, y, text, attr))

    def plotlegend(self, i, txt, attr):
        self.plotlabel(self.plotwidth-30, i*4, txt, attr)

    @property
    def plotterCursorBox(self):
        'Returns pixel bounds of cursor as a Box.  Override to provide a cursor.'
        return Box(0,0,0,0)

    @property
    def plotterMouseX(self):
        return self.mouseX*2

    @property
    def plotterMouseY(self):
        return self.mouseY*4


    def getPixelAttrRandom(self, x, y):
        'weighted-random choice of attr at this pixel.'
        c = list(attr for attr, rows in self.pixels[y][x].items()
                         for r in rows if attr not in self.disabledAttrs)
        return random.choice(c) if c else 0

    def getPixelAttrMost(self, x, y):
        'most common attr at this pixel.'
        r = self.pixels[y][x]
        c = sorted((len(rows), attr, rows) for attr, rows in r.items() if attr not in self.disabledAttrs)
        if not c:
            return 0
        _, attr, rows = c[-1]
        if anySelected(self.source, rows):
            attr, _ = colors.update(attr, 8, 'bold', 10)
        return attr

    def togglePixelAttrs(self, attr):
        if attr in self.disabledAttrs:
            self.disabledAttrs.remove(attr)
        else:
            self.disabledAttrs.add(attr)
        self.plotlegends()

    def getRowsInside(self, bbox):
        ret = {}
        for r in self.genRowsInside(bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax):
            ret[id(r)] = r
        return list(ret.values())

    def genRowsInside(self, x1, y1, x2, y2):
        for y in range(y1, y2):
            for x in range(x1, x2):
                for attr, rows in self.pixels[y][x].items():
                    for r in rows:
                        yield r

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

                    if cursorBBox.within(char_x*2, char_y*4) or \
                       cursorBBox.within(char_x*2+1, char_y*4+3):
                        attr, _ = colors.update(attr, 0, options.color_current_row, 10)

                    if attr:
                        scr.addstr(char_y, char_x, chr(0x2800+braille_num), attr)

        if options.show_graph_labels:
            for pix_x, pix_y, txt, attr in self.labels:
                clipdraw(scr, int(pix_y/4), int(pix_x/2), txt, attr, len(txt))


# - has a cursor, of arbitrary position and width/height (not restricted to current zoom)
class Canvas(Plotter):
    'zoomable/scrollable virtual canvas with (x,y) coordinates in arbitrary units'
    rowtype = 'plots'
    aspectRatio = None
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

        Command('-', 'tmp=(cursorBox.xcenter, cursorBox.ycenter); setZoom(zoomlevel*options.zoom_incr); fixPoint(plotviewCenterX, plotviewCenterY, *tmp)', 'zoom into cursor center'),
        Command('+', 'tmp=(cursorBox.xcenter, cursorBox.ycenter); setZoom(zoomlevel/options.zoom_incr); fixPoint(plotviewCenterX, plotviewCenterY, *tmp)', 'zoom into cursor center'),
        Command('_', 'sheet.canvasBox = None; sheet.visibleBox = None; setZoom(1.0); refresh()', 'zoom to fit full extent'),

        # set cursor box with left click
        Command('BUTTON1_PRESSED', 'sheet.cursorBox = Box(*canvasMouseXY.xy)', 'start cursor box with left mouse button press'),
        Command('BUTTON1_RELEASED', 'setCursorSize(*canvasMouseXY.xy)', 'end cursor box with left mouse button release'),

        Command('BUTTON3_PRESSED', 'sheet.gridAnchorXY = canvasMouseXY.xy', 'mark grid point to move'),
        Command('BUTTON3_RELEASED', 'fixPoint(plotterMouseX, plotterMouseY, *gridAnchorXY)', 'mark canvas anchor point'),

        Command('BUTTON4_PRESSED', 'tmp=canvasMouseXY; setZoom(zoomlevel/options.zoom_incr); fixPoint(plotterMouseX, plotterMouseY, *tmp.xy)', 'zoom in with scroll wheel'),
        Command('REPORT_MOUSE_POSITION', 'tmp=canvasMouseXY; setZoom(zoomlevel*options.zoom_incr); fixPoint(plotterMouseX, plotterMouseY, *tmp.xy)', 'zoom out with scroll wheel'),

        Command('s', 'source.select(list(getRowsInside(plotterCursorBox)))', 'select rows on source sheet contained within canvas cursor'),
        Command('t', 'source.unselect(list(getRowsInside(plotterCursorBox)))', 'toggle selection of rows on source sheet contained within canvas cursor'),
        Command('u', 'source.unselect(list(getRowsInside(plotterCursorBox)))', 'unselect rows on source sheet contained within canvas cursor'),
        Command(ENTER, 'vs=copy(source); vs.rows=list(getRowsInside(plotterCursorBox)); vd.push(vs)', 'Open sheet of source rows contained within canvas cursor'),


        Command('gs', 'source.select(list(getRowsInside(plotterVisibleBox)))', 'select rows visible on screen'),
        Command('gt', 'source.unselect(list(getRowsInside(plotterVisibleBox)))', 'toggle selection of rows visible on screen'),
        Command('gu', 'source.unselect(list(getRowsInside(plotterVisibleBox)))', 'unselect rows visible on screen'),
        Command('g'+ENTER, 'vs=copy(source); vs.rows=list(getRowsInside(plotterVisibleBox)); vd.push(vs)', 'open sheet of source rows visible on screen'),
    ]

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)

        # bounding box of entire canvas in canvas units, updated when adding point/line/label or recalcBounds
        self.canvasBox = None  # derive first bounds on first draw

        # bounding box of visible canvas, in canvas units
        self.visibleBox = None

        # bounding box of cursor
        self.cursorBox = None # Box(0, 0, 0, 0)

        self.zoomlevel = 1.0
        self.needsRefresh = False

        self.gridpoints = []  # list of (grid_x, grid_y, attr, row)
        self.gridlines = []   # list of (grid_x1, grid_y1, grid_x2, grid_y2, attr, row)
        self.gridlabels = []  # list of (grid_x, grid_y, label, attr, row)

        self.legends = collections.OrderedDict()   # txt: attr  (visible legends only)
        self.plotAttrs = {}   # key: attr  (all keys, for speed)
        self.reset()

    def __len__(self):
        return len(self.gridpoints) + len(self.gridlines)

    def reset(self):
        self.legends.clear()
        self.plotAttrs.clear()
        self.unusedAttrs = list(colors[colorname] for colorname in options.plot_colors.split())

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
        self.plotviewMinX = self.leftMarginPixels
        self.plotviewMinY = self.topMarginPixels
        self.plotviewWidth = self.plotwidth - self.rightMarginPixels - self.leftMarginPixels
        self.plotviewHeight = self.plotheight - self.bottomMarginPixels - self.topMarginPixels

    @property
    def statusLine(self):
        return 'canvas %s visible %s cursor %s' % (self.canvasBox, self.visibleBox, self.cursorBox)

    @property
    def canvasMouseXY(self):
        return Point(self.visibleBox.xmin + (self.plotterMouseX-self.plotviewMinX)/self.xScaler,
                     self.visibleBox.ymin + (self.plotterMouseY-self.plotviewMinY)/self.yScaler)

    def setCursorSize(self, gridX, gridY):
        'sets width based on other side x and y'
        if gridX > self.cursorBox.xmin:
            self.cursorBox.w = max(gridX - self.cursorBox.xmin, self.canvasCharWidth)
        else:
            self.cursorBox.w = max(self.cursorBox.xmin - gridX, self.canvasCharWidth)
            self.cursorBox.xmin = gridX

        if gridY > self.cursorBox.ymin:
            self.cursorBox.h = max(gridY - self.cursorBox.ymin, self.canvasCharHeight)
        else:
            self.cursorBox.h = max(self.cursorBox.ymin - gridY, self.canvasCharHeight)
            self.cursorBox.ymin = gridY

    @property
    def canvasCharWidth(self):
        'Width in canvas units of a single char in the terminal'
        return self.visibleBox.w*2/self.plotviewWidth

    @property
    def canvasCharHeight(self):
        'Height in canvas units of a single char in the terminal'
        return self.visibleBox.h*4/self.plotviewHeight

    @property
    def plotviewCenterX(self):
        return self.plotviewMinX + self.plotviewWidth/2

    @property
    def plotviewCenterY(self):
        return self.plotviewMinY + self.plotviewHeight/2

    @property
    def plotviewMaxY(self):
        return self.plotviewMinY + self.plotviewHeight

    @property
    def plotviewMaxX(self):
        return self.plotviewMinX + self.plotviewWidth

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
        self.gridpoints.append((x, y, attr, row))

    def line(self, x1, y1, x2, y2, attr, row=None):
        self.gridlines.append((x1, y1, x2, y2, attr, row))

    def polyline(self, vertices, attr, row=None):
        'adds lines for (x,y) vertices of a polygon'
        prev_x, prev_y = vertices[0]
        for x, y in vertices[1:]:
            self.line(prev_x, prev_y, x, y, attr, row)
            prev_x, prev_y = x, y

    def polygon(self, vertices, attr, row=None):
        'adds lines for (x,y) vertices of a polygon'
        prev_x, prev_y = vertices[-1]
        for x, y in vertices:
            self.line(prev_x, prev_y, x, y, attr, row)
            prev_x, prev_y = x, y

    def label(self, x, y, text, attr, row=None):
        self.gridlabels.append((x, y, text, attr, row))

    def fixPoint(self, plotter_x, plotter_y, canvas_x, canvas_y):
        'adjust visibleMinX/Y so that (grid_x, grid_y) is plotted at (canvas_x, canvas_y)'
        self.visibleBox.xmin = canvas_x - self.gridW(plotter_x-self.plotviewMinX)
        self.visibleBox.ymin = canvas_y - self.gridH(plotter_y-self.plotviewMinY)
        self.refresh()

    def zoomTo(self, bbox):
        'set visible area to bbox, maintaining aspectRatio if applicable'
        self.fixPoint(self.plotviewMinX, self.plotviewMinY, bbox.xmin, bbox.ymin)
        self.zoomlevel=max(bbox.w/self.canvasBox.w, bbox.h/self.canvasBox.h)

    def setZoom(self, zoomlevel=None):
        if zoomlevel:
            self.zoomlevel = zoomlevel

        self.resetBounds()
        self.plotlegends()

    def resetBounds(self):
        if not self.canvasBox:
            xmins = []
            ymins = []
            xmaxs = []
            ymaxs = []
            if self.gridpoints:
                xmins.append(min(x for x, y, attr, row in self.gridpoints))
                xmaxs.append(max(x for x, y, attr, row in self.gridpoints))
                ymins.append(min(y for x, y, attr, row in self.gridpoints))
                ymaxs.append(max(y for x, y, attr, row in self.gridpoints))
            if self.gridlines:
                xmins.append(min(min(x1, x2) for x1, y1, x2, y2, attr, row in self.gridlines))
                xmaxs.append(max(max(x1, x2) for x1, y1, x2, y2, attr, row in self.gridlines))
                ymins.append(min(min(y1, y2) for x1, y1, x2, y2, attr, row in self.gridlines))
                ymaxs.append(max(max(y1, y2) for x1, y1, x2, y2, attr, row in self.gridlines))

            if xmins:
                self.canvasBox = BoundingBox(min(xmins), min(ymins), max(xmaxs), max(ymaxs))
            else:
                self.canvasBox = Box(0, 0, 1.0, 1.0)  # just something

        if not self.visibleBox:
            # initialize minx/miny, but w/h must be set first
            self.visibleBox = Box(0, 0, self.plotviewWidth/self.xScaler, self.plotviewHeight/self.yScaler)
            self.visibleBox.xmin = self.canvasBox.xcenter - self.visibleBox.w/2
            self.visibleBox.ymin = self.canvasBox.ycenter - self.visibleBox.h/2
        else:
            self.visibleBox.w = self.plotviewWidth/self.xScaler
            self.visibleBox.h = self.plotviewHeight/self.yScaler

        if not self.cursorBox:
            self.cursorBox = Box(self.visibleBox.xmin, self.visibleBox.ymin, self.canvasCharWidth, self.canvasCharHeight)

    def plotlegends(self):
        # display labels
        for i, (legend, attr) in enumerate(self.legends.items()):
            self._commands[str(i+1)] = Command(str(i+1), 'togglePixelAttrs(%s)' % attr, '')
            if attr in self.disabledAttrs:
                attr = colors['238 blue']
            self.plotlegend(i, '%s.%s'%(i+1,legend), attr)

    def checkCursor(self):
        'override Sheet.checkCursor'
        return False

    @property
    def xScaler(self):
        xratio = self.plotviewWidth/(self.canvasBox.w*self.zoomlevel)
        if self.aspectRatio:
            yratio = self.plotviewHeight/(self.canvasBox.h*self.zoomlevel)
            return self.aspectRatio*min(xratio, yratio)
        else:
            return xratio

    @property
    def yScaler(self):
        yratio = self.plotviewHeight/(self.canvasBox.h*self.zoomlevel)
        if self.aspectRatio:
            xratio = self.plotviewWidth/(self.canvasBox.w*self.zoomlevel)
            return min(xratio, yratio)
        else:
            return yratio

    def scaleX(self, x):
        'returns plotter x coordinate'
        return round(self.plotviewMinX+(x-self.visibleBox.xmin)*self.xScaler)

    def scaleY(self, y):
        'returns plotter y coordinate'
        return round(self.plotviewMinY+(y-self.visibleBox.ymin)*self.yScaler)

    def gridW(self, plotter_width):
        'plotter X units to canvas units'
        return plotter_width/self.xScaler

    def gridH(self, plotter_height):
        'plotter Y units to canvas units'
        return plotter_height/self.yScaler

    def refresh(self):
        'triggers render() on next draw()'
        self.needsRefresh = True

    def render(self):
        'resets plotter, cancels previous render threads, spawns a new render'
        self.needsRefresh = False
        cancelThread(*(t for t in self.currentThreads if t.name == 'plotAll_async'))
        self.pixels.clear()
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
        gridxmin, gridymin = self.plotviewMinX, self.plotviewMinY

        for x, y, attr, row in Progress(self.gridpoints):
            if ymin <= y and y <= ymax:
                if xmin <= x and x <= xmax:
                    x = gridxmin+(x-xmin)*xfactor
                    y = gridymin+(y-ymin)*yfactor
                    self.plotpixel(round(x), round(y), attr, row)

        for x1, y1, x2, y2, attr, row in Progress(self.gridlines):
            r = clipline(x1, y1, x2, y2, xmin, ymin, xmax, ymax)
            if r:
                x1, y1, x2, y2 = r
                x1 = gridxmin+(x1-xmin)*xfactor
                y1 = gridymin+(y1-ymin)*yfactor
                x2 = gridxmin+(x2-xmin)*xfactor
                y2 = gridymin+(y2-ymin)*yfactor
                self.plotline(x1, y1, x2, y2, attr, row)

        for x, y, text, attr, row in Progress(self.gridlabels):
            self.plotlabel(self.scaleX(x), self.scaleY(y), text, attr, row)

