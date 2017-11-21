
from collections import defaultdict, Counter
from visidata import *

# The Canvas covers the entire terminal (minus the status line).
# The Grid is arbitrarily large (a virtual cartesian coordinate system).
# The visibleGrid is what is actively drawn onto the terminal.
# The gridCanvas is the area of the canvas that contains that visibleGrid.
# The gridAxes are drawn outside the gridCanvas, on the left and bottom.

# Canvas and gridCanvas coordinates are pixels at the same scale (gridCanvas are offset to leave room for axes).
# Grid and visibleGrid coordinates are app-specific units.

# plotpixel()/plotline()/plotlabel() take Canvas pixel coordinates
# point()/line()/label() take Grid coordinates

option('show_graph_labels', True, 'show axes and legend on graph')
option('plot_colors', 'green red yellow cyan magenta white 38 136 168', 'list of distinct colors to use for plotting distinct objects')
option('disp_pixel_random', False, 'randomly choose attr from set of pixels instead of most common')
option('zoom_incr', 2.0, 'amount to multiply current zoomlevel by when zooming')

# pixels covering whole actual terminal
#  - width/height are exactly equal to the number of pixels displayable, and can change at any time.
#  - needs to refresh from source on resize
#  - all x/y/w/h in PixelCanvas are pixel coordinates
#  - override cursorPixelBounds to specify a cursor
class PixelCanvas(Sheet):
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
        self.canvasMinY = 0
        self.canvasMinX = 0
        self.canvasWidth = vd().windowWidth*2
        self.canvasHeight = (vd().windowHeight-1)*4  # exclude status line

        # pixels[y][x] = { attr: list(rows), ... }
        self.pixels = [[defaultdict(list) for x in range(self.canvasWidth)] for y in range(self.canvasHeight)]

    def plotpixel(self, x, y, attr, row=None):
        self.pixels[round(y)][round(x)][attr].append(row)

    @staticmethod
    def clipline(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
        'Liang-Barsky algorithm'
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

    def plotline(self, x1, y1, x2, y2, attr, row=None):
        for x, y in self.iterline(x1, y1, x2, y2):
            self.plotpixel(x, y, attr, row)

    @staticmethod
    def iterline(x1, y1, x2, y2):
        'Draws onscreen segment of line from (x1, y1) to (x2, y2)'
        xdiff = abs(x2-x1)
        ydiff = abs(y2-y1)
        xdir = 1 if x1 <= x2 else -1
        ydir = 1 if y1 <= y2 else -1

        r = round(max(xdiff, ydiff))

        if r == 0:  # point, not line
            yield x1, y1
        else:
            x, y = x1, y1
            for i in range(r+1):
                x += xdir * xdiff / r
                y += ydir * ydiff / r

                yield x, y

    def plotlabel(self, x, y, text, attr):
        self.labels.append((x, y, text, attr))

    def plotlegend(self, i, txt, attr):
        self.plotlabel(self.canvasWidth-30, i*4, txt, attr)

    @property
    def cursorPixelBounds(self):
        'Returns pixel bounds of cursor as [ left, top, right, bottom ]'
        return [ 0, 0, 0, 0 ]

    def withinBounds(self, x, y, bbox):
        left, top, right, bottom = bbox
        return x >= left and \
               x < right and \
               y >= top and \
               y < bottom

    def getPixelAttrRandom(self, x, y):
        'weighted-random choice of attr at this pixel.'
        c = list(attr for attr, rows in self.pixels[y][x].items()
                         for r in rows if attr not in self.disabledAttrs)
        return random.choice(c) if c else 0

    def getPixelAttrMost(self, x, y):
        'most common attr at this pixel.'
        r = self.pixels[y][x]
        c = sorted((len(rows), attr) for attr, rows in r.items() if attr not in self.disabledAttrs)
        return c[-1][1] if c else 0

    def togglePixelAttrs(self, attr):
        if attr in self.disabledAttrs:
            self.disabledAttrs.remove(attr)
        else:
            self.disabledAttrs.add(attr)
        self.plotlegends()

    def getRowsInside(self, x1, y1, x2, y2):
        for y in range(y1, y2):
            for x in range(x1, x2):
                for attr, rows in self.pixels[y][x].items():
                    for r in rows:
                        yield r

    def draw(self, scr):
        if self.needsRefresh:
            self.plotAll()

        scr.erase()

        if self.pixels:
            cursorBBox = self.cursorPixelBounds
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

                    if self.withinBounds(char_x*2, char_y*4, cursorBBox) or \
                       self.withinBounds(char_x*2+1, char_y*4+3, cursorBBox):
                        attr, _ = colors.update(attr, 0, options.color_current_row, 10)

                    if attr:
                        scr.addstr(char_y, char_x, chr(0x2800+braille_num), attr)

        if options.show_graph_labels:
            for pix_x, pix_y, txt, attr in self.labels:
                clipdraw(scr, int(pix_y/4), int(pix_x/2), txt, attr, len(txt))


# virtual display of arbitrary dimensions
# - x/y/w/h are always in grid units (units convenient to the app)
# - allows zooming in/out
# - has a cursor, of arbitrary position and width/height (not restricted to current zoom)
class GridCanvas(PixelCanvas):
    rowtype = 'plots'
    aspectRatio = None
    leftMarginPixels = 10*2
    rightMarginPixels = 6*2
    topMarginPixels = 0
    bottomMarginPixels = 2*4  # reserve bottom line for x axis

    commands = PixelCanvas.commands + [
        Command('move-left', 'sheet.cursorGridMinX -= cursorGridWidth', ''),
        Command('move-right', 'sheet.cursorGridMinX += cursorGridWidth', ''),
        Command('move-down', 'sheet.cursorGridMinY += cursorGridHeight', ''),
        Command('move-up', 'sheet.cursorGridMinY -= cursorGridHeight', ''),

        Command('zh', 'sheet.cursorGridMinX -= charGridWidth', ''),
        Command('zl', 'sheet.cursorGridMinX += charGridWidth', ''),
        Command('zj', 'sheet.cursorGridMinY += charGridHeight', ''),
        Command('zk', 'sheet.cursorGridMinY -= charGridHeight', ''),

        Command('gH', 'sheet.cursorGridWidth /= 2', ''),
        Command('gL', 'sheet.cursorGridWidth *= 2', ''),
        Command('gJ', 'sheet.cursorGridHeight /= 2', ''),
        Command('gK', 'sheet.cursorGridHeight *= 2', ''),

        Command('H', 'sheet.cursorGridWidth -= charGridWidth', ''),
        Command('L', 'sheet.cursorGridWidth += charGridWidth', ''),
        Command('J', 'sheet.cursorGridHeight += charGridHeight', ''),
        Command('K', 'sheet.cursorGridHeight -= charGridHeight', ''),

        Command('zz', 'zoomTo(cursorGridMinX, cursorGridMinY, cursorGridMaxX, cursorGridMaxY)', 'set visible bounds to cursor'),

        Command('-', 'tmp=(cursorGridCenterX, cursorGridCenterY); setZoom(zoomlevel*options.zoom_incr); fixPoint(gridCanvasCenterX, gridCanvasCenterY, *tmp)', 'zoom into cursor center'),
        Command('+', 'tmp=(cursorGridCenterX, cursorGridCenterY); setZoom(zoomlevel/options.zoom_incr); fixPoint(gridCanvasCenterX, gridCanvasCenterY, *tmp)', 'zoom into cursor center'),
        Command('_', 'sheet.gridWidth = 0; sheet.visibleGridWidth = 0; setZoom(1.0); refresh()', 'zoom to fit full extent'),

        # set cursor box with left click
        Command('BUTTON1_PRESSED', 'sheet.cursorGridMinX, sheet.cursorGridMinY = gridMouseX, gridMouseY; sheet.cursorGridWidth=0', 'start cursor box with left mouse button press'),
        Command('BUTTON1_RELEASED', 'setCursorSize(gridMouseX, gridMouseY)', 'end cursor box with left mouse button release'),

        Command('BUTTON3_PRESSED', 'sheet.gridAnchorXY = (gridMouseX, gridMouseY)', 'mark grid point to move'),
        Command('BUTTON3_RELEASED', 'fixPoint(canvasMouseX, canvasMouseY, *gridAnchorXY)', 'mark canvas anchor point'),

        Command('BUTTON4_PRESSED', 'tmp=(gridMouseX,gridMouseY); setZoom(zoomlevel/options.zoom_incr); fixPoint(canvasMouseX, canvasMouseY, *tmp)', 'zoom in with scroll wheel'),
        Command('REPORT_MOUSE_POSITION', 'tmp=(gridMouseX,gridMouseY); setZoom(zoomlevel*options.zoom_incr); fixPoint(canvasMouseX, canvasMouseY, *tmp)', 'zoom out with scroll wheel'),

        Command('s', 'source.select(list(getRowsInside(*cursorPixelBounds)))', 'select all points within cursor box'),
        Command('t', 'source.unselect(list(getRowsInside(*cursorPixelBounds)))', 'toggle selection of all points within cursor box'),
        Command('u', 'source.unselect(list(getRowsInside(*cursorPixelBounds)))', 'unselect all points within cursor box'),
        Command(ENTER, 'vs=copy(source); vs.rows=list(getRowsInside(*cursorPixelBounds)); vd.push(vs)', ''),


        Command('gs', 'source.select(list(getRowsInside(*visiblePixelBounds)))', 'select all points visible onscreen'),
        Command('gt', 'source.unselect(list(getRowsInside(*visiblePixelBounds)))', 'toggle selection of all points visible onscreen'),
        Command('gu', 'source.unselect(list(getRowsInside(*visiblePixelBounds)))', 'unselect all points visible onscreen'),
        Command('g'+ENTER, 'vs=copy(source); vs.rows=list(getRowsInside(*visiblePixelBounds)); vd.push(vs)', ''),
    ]

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)

        # bounding box of entire grid in grid units, updated when adding point/line/label or recalcBounds
        self.gridMinX, self.gridMinY = None, None  # derive first bounds on first draw
        self.gridWidth, self.gridHeight = None, None

        # bounding box of visible grid, in grid units
        self.visibleGridMinX = None
        self.visibleGridMinY = None
        self.visibleGridWidth = None
        self.visibleGridHeight = None

        # bounding box of cursor (should be contained within visible grid?)
        self.cursorGridMinX, self.cursorGridMinY = 0, 0
        self.cursorGridWidth, self.cursorGridHeight = None, None

        self.zoomlevel = 1.0
        self.needsRefresh = False

        # bounding box of gridCanvas, in pixels
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
                attr = self.unusedAttrs.pop()
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
        self.gridCanvasMinX = self.leftMarginPixels
        self.gridCanvasMinY = self.topMarginPixels
        self.gridCanvasWidth = self.canvasWidth - self.rightMarginPixels - self.leftMarginPixels
        self.gridCanvasHeight = self.canvasHeight - self.bottomMarginPixels - self.topMarginPixels

    @property
    def statusLine(self):
        gridstr = 'grid (%s,%s)-(%s,%s)' % (self.gridMinX, self.gridMinY, self.gridMaxX, self.gridMaxY)
        vgridstr = 'visibleGrid (%s,%s)-(%s,%s)' % (self.visibleGridMinX, self.visibleGridMinY, self.visibleGridMaxX, self.visibleGridMaxY)
        cursorstr = 'cursor (%s,%s)-(%s,%s)' % (self.cursorGridMinX, self.cursorGridMinY, self.cursorGridMaxX, self.cursorGridMaxY)
        return ' '.join((gridstr, vgridstr, cursorstr))

    @property
    def canvasMouseX(self):
        return self.mouseX*2

    @property
    def canvasMouseY(self):
        return self.mouseY*4

    @property
    def gridMouseX(self):
        return self.visibleGridMinX + (self.canvasMouseX-self.gridCanvasMinX)/self.xScaler

    @property
    def gridMouseY(self):
        return self.visibleGridMinY + (self.canvasMouseY-self.gridCanvasMinY)/self.yScaler

    def setCursorSize(self, gridX, gridY):
        'sets width based on other side x and y'
        if gridX > self.cursorGridMinX:
            self.cursorGridWidth = max(gridX - self.cursorGridMinX, self.charGridWidth)
        else:
            self.cursorGridWidth = max(self.cursorGridMinX - gridX, self.charGridWidth)
            self.cursorGridMinX = gridX

        if gridY > self.cursorGridMinY:
            self.cursorGridHeight = max(gridY - self.cursorGridMinY, self.charGridHeight)
        else:
            self.cursorGridHeight = max(self.cursorGridMinY - gridY, self.charGridHeight)
            self.cursorGridMinY = gridY

    @property
    def charGridWidth(self):
        'Width in grid units of a single char in the terminal'
        return self.visibleGridWidth*2/self.gridCanvasWidth

    @property
    def charGridHeight(self):
        'Height in grid units of a single char in the terminal'
        return self.visibleGridHeight*4/self.gridCanvasHeight

    @property
    def gridCanvasCenterX(self):
        return self.gridCanvasMinX + self.gridCanvasWidth/2

    @property
    def gridCanvasCenterY(self):
        return self.gridCanvasMinY + self.gridCanvasHeight/2

    @property
    def gridMaxX(self):
        return self.gridMinX + self.gridWidth

    @property
    def gridMaxY(self):
        return self.gridMinY + self.gridHeight

    @property
    def cursorGridCenterX(self):
        return self.cursorGridMinX + self.cursorGridWidth/2

    @property
    def cursorGridCenterY(self):
        return self.cursorGridMinY + self.cursorGridHeight/2

    @property
    def cursorGridMaxX(self):
        return self.cursorGridMinX + self.cursorGridWidth

    @property
    def cursorGridMaxY(self):
        return self.cursorGridMinY + self.cursorGridHeight

    @property
    def visibleGridMaxX(self):
        return self.visibleGridMinX + self.visibleGridWidth

    @property
    def visibleGridMaxY(self):
        return self.visibleGridMinY + self.visibleGridHeight

    @property
    def gridCanvasMaxY(self):
        return self.gridCanvasMinY + self.gridCanvasHeight

    @property
    def gridCanvasMaxX(self):
        return self.gridCanvasMinX + self.gridCanvasWidth

    @property
    def cursorGridBounds(self):
        return [ self.cursorGridMinX,
                 self.cursorGridMinY,
                 self.cursorGridMaxX,
                 self.cursorGridMaxY
        ]

    @property
    def visibleGridBounds(self):
        return [ self.visibleGridMinX,
                 self.visibleGridMinY,
                 self.visibleGridMinX+self.visibleGridWidth,
                 self.visibleGridMinY+self.visibleGridHeight
        ]

    @property
    def visiblePixelBounds(self):
        return [ self.scaleX(self.visibleGridMinX),
                 self.scaleY(self.visibleGridMinY),
                 self.scaleX(self.visibleGridMinX+self.visibleGridWidth),
                 self.scaleY(self.visibleGridMinY+self.visibleGridHeight)
        ]

    @property
    def cursorPixelBounds(self):
        if self.cursorGridWidth is None:
            return [0,0,0,0]
        return [ self.scaleX(self.cursorGridMinX),
                 self.scaleY(self.cursorGridMinY),
                 self.scaleX(self.cursorGridMinX+self.cursorGridWidth),
                 self.scaleY(self.cursorGridMinY+self.cursorGridHeight)
        ]

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

    def fixPoint(self, canvas_x, canvas_y, grid_x, grid_y):
        'adjust visibleGrid so that (grid_x, grid_y) is plotted at (canvas_x, canvas_y)'
        self.visibleGridMinX = grid_x - self.gridW(canvas_x-self.gridCanvasMinX)
        self.visibleGridMinY = grid_y - self.gridH(canvas_y-self.gridCanvasMinY)
        self.refresh()

    def zoomTo(self, x1, y1, x2, y2):
        self.fixPoint(self.gridCanvasMinX, self.gridCanvasMinY, x1, y1)
        self.zoomlevel=max(self.cursorGridWidth/self.gridWidth, self.cursorGridHeight/self.gridHeight)

    def setZoom(self, zoomlevel=None):
        if zoomlevel:
            self.zoomlevel = zoomlevel

        self.resetBounds()
        self.plotlegends()

    def resetBounds(self):
        if not self.gridWidth or not self.gridHeight:
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
                self.gridMinX = min(xmins)
                self.gridMinY = min(ymins)
                self.gridWidth = max(xmaxs) - self.gridMinX
                self.gridHeight = max(ymaxs) - self.gridMinY
            else:
                self.gridWidth = 1.0
                self.gridHeight = 1.0

        if not self.visibleGridWidth or not self.visibleGridHeight:
            # initialize minx/miny, but w/h must be set first
            self.visibleGridWidth = self.gridCanvasWidth/self.xScaler
            self.visibleGridHeight = self.gridCanvasHeight/self.yScaler
            self.visibleGridMinX = self.gridMinX + self.gridWidth/2 - self.visibleGridWidth/2
            self.visibleGridMinY = self.gridMinY + self.gridHeight/2 - self.visibleGridHeight/2
        else:
            self.visibleGridWidth = self.gridCanvasWidth/self.xScaler
            self.visibleGridHeight = self.gridCanvasHeight/self.yScaler

        if not self.cursorGridWidth or not self.cursorGridHeight:
            self.cursorGridMinX = self.visibleGridMinX
            self.cursorGridMinY = self.visibleGridMinY
            self.cursorGridWidth = self.charGridWidth
            self.cursorGridHeight = self.charGridHeight

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
        xratio = self.gridCanvasWidth/(self.gridWidth*self.zoomlevel)
        if self.aspectRatio:
            yratio = self.gridCanvasHeight/(self.gridHeight*self.zoomlevel)
            return self.aspectRatio*min(xratio, yratio)
        else:
            return xratio

    @property
    def yScaler(self):
        yratio = self.gridCanvasHeight/(self.gridHeight*self.zoomlevel)
        if self.aspectRatio:
            xratio = self.gridCanvasWidth/(self.gridWidth*self.zoomlevel)
            return self.aspectRatio*min(xratio, yratio)
        else:
            return yratio

    def scaleX(self, x):
        'returns canvas x coordinate'
        return round(self.gridCanvasMinX+(x-self.visibleGridMinX)*self.xScaler)

    def scaleY(self, y):
        'returns canvas y coordinate'
        return round(self.gridCanvasMinY+(y-self.visibleGridMinY)*self.yScaler)

    def gridW(self, canvas_width):
        'canvas X units to grid units'
        return canvas_width/self.xScaler

    def gridH(self, canvas_height):
        'canvas Y units to grid units'
        return canvas_height/self.yScaler

    def refresh(self):
        self.needsRefresh = True

    def plotAll(self):
        self.needsRefresh = False
        cancelThread(*(t for t in self.currentThreads if t.name == 'plotAll_async'))
        self.pixels.clear()
        self.labels.clear()
        self.resetCanvasDimensions()
        self.plotAll_async()

    @async
    def plotAll_async(self):
        'plots points and lines and text onto the PixelCanvas'

        self.setZoom()

        xmin, ymin, xmax, ymax = self.visibleGridBounds
        xfactor, yfactor = self.xScaler, self.yScaler
        gridxmin, gridymin = self.gridCanvasMinX, self.gridCanvasMinY

        for x, y, attr, row in Progress(self.gridpoints):
            if ymin <= y and y <= ymax:
                if xmin <= x and x <= xmax:
                    x = gridxmin+(x-xmin)*xfactor
                    y = gridymin+(y-ymin)*yfactor
                    self.plotpixel(x, y, attr, row)

        for x1, y1, x2, y2, attr, row in Progress(self.gridlines):
            r = self.clipline(x1, y1, x2, y2, xmin, ymin, xmax, ymax)
            if r:
                x1, y1, x2, y2 = r
                x1 = gridxmin+(x1-xmin)*xfactor
                y1 = gridymin+(y1-ymin)*yfactor
                x2 = gridxmin+(x2-xmin)*xfactor
                y2 = gridymin+(y2-ymin)*yfactor
                self.plotline(x1, y1, x2, y2, attr, row)

        for x, y, text, attr, row in Progress(self.gridlabels):
            self.plotlabel(self.scaleX(x), self.scaleY(y), text, attr, row)

