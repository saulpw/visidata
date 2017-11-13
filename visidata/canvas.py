
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


# pixels covering whole actual terminal
#  - width/height are exactly equal to the number of pixels displayable, and can change at any time.
#  - needs to refresh from source on resize
#  - all x/y/w/h in PixelCanvas are pixel coordinates
#  - override cursorPixelBounds to specify a cursor (none by default)
class PixelCanvas(Sheet):
    columns=[Column('')]  # to eliminate errors outside of draw()
    commands=[
        Command('^L', 'refresh()', 'redraw all pixels on canvas'),
        Command('w', 'options.show_graph_labels = not options.show_graph_labels', 'toggle show_graph_labels'),
        Command('KEY_RESIZE', 'refresh()', ''),
    ]
    def __init__(self, name, *sources, **kwargs):
        super().__init__(name, *sources, **kwargs)
        self.pixels = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) # [y][x] = { attr: list(rows), ... }
        self.labels = []  # (x, y, text, attr)
        self.resetCanvasDimensions()

    def resetCanvasDimensions(self):
        'sets total available canvas dimensions'
        self.canvasTop = 0
        self.canvasLeft = 0
        self.canvasWidth = vd().windowWidth*2
        self.canvasHeight = (vd().windowHeight-1)*4  # exclude status line

    def plotpixel(self, x, y, attr, row=None):
        self.pixels[round(y)][round(x)][attr].append(row)

    def plotline(self, x1, y1, x2, y2, attr, row=None):
        'Draws onscreen segment of line from (x1, y1) to (x2, y2)'
        xdiff = max(x1, x2) - min(x1, x2)
        ydiff = max(y1, y2) - min(y1, y2)
        xdir = 1 if x1 <= x2 else -1
        ydir = 1 if y1 <= y2 else -1

        r = round(max(xdiff, ydiff))

        for i in range(r+1):
            x = x1
            y = y1

            if r:
                y += ydir * (i * ydiff) / r
                x += xdir * (i * xdiff) / r

            self.plotpixel(round(x), round(y), attr, row)

    def plotlabel(self, x, y, text, attr):
        self.labels.append((x, y, text, attr))

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

    def getPixelAttr(self, x, y):
        r = self.pixels[y].get(x, None)
        if not r:
            return 0
        c = Counter({attr: len(rows) for attr, rows in r.items()})
        return c.most_common(1)[0][0]

    def getRowsInside(self, x1, y1, x2, y2):
        for y in range(y1, y2):
            for x in range(x1, x2):
                for attr, rows in self.pixels[y].get(x, {}).items():
                    for r in rows:
                        yield r

    def draw(self, scr):
        scr.erase()
        if self.needsRefresh:
            self.plotAll()

        if self.pixels:
            cursorBBox = self.cursorPixelBounds

            for char_y in range(0, self.nVisibleRows+1):
                for char_x in range(0, vd().windowWidth):
                    block_attrs = [
                        self.getPixelAttr(char_x*2  , char_y*4  ),
                        self.getPixelAttr(char_x*2  , char_y*4+1),
                        self.getPixelAttr(char_x*2  , char_y*4+2),
                        self.getPixelAttr(char_x*2+1, char_y*4  ),
                        self.getPixelAttr(char_x*2+1, char_y*4+1),
                        self.getPixelAttr(char_x*2+1, char_y*4+2),
                        self.getPixelAttr(char_x*2  , char_y*4+3),
                        self.getPixelAttr(char_x*2+1, char_y*4+3),
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

                    scr.addstr(char_y, char_x, chr(0x2800+braille_num), attr)

        if options.show_graph_labels:
            for pix_x, pix_y, txt, attr in self.labels:
                clipdraw(scr, int(pix_y/4), int(pix_x/2), txt, attr, len(txt))


# virtual display of arbitrary dimensions
# - x/y/w/h are always in grid units (units convenient to the app)
# - allows zooming in/out
# - has a cursor, of arbitrary position and width/height (not restricted to current zoom)
class GridCanvas(PixelCanvas):
    leftMarginPixels = 10*2
    rightMarginPixels = 6*2
    topMarginPixels = 0
    bottomMarginPixels = 2*4  # reserve bottom line for x axis

    commands = PixelCanvas.commands + [
        Command('move-left', 'sheet.cursorGridLeft -= cursorGridWidth', ''),
        Command('move-right', 'sheet.cursorGridLeft += cursorGridWidth', ''),
        Command('move-down', 'sheet.cursorGridTop += cursorGridHeight', ''),
        Command('move-up', 'sheet.cursorGridTop -= cursorGridHeight', ''),

        Command('zh', 'sheet.cursorGridLeft -= charGridWidth', ''),
        Command('zl', 'sheet.cursorGridLeft += charGridWidth', ''),
        Command('zj', 'sheet.cursorGridTop += charGridHeight', ''),
        Command('zk', 'sheet.cursorGridTop -= charGridHeight', ''),

        Command('gH', 'sheet.cursorGridWidth /= 2', ''),
        Command('gL', 'sheet.cursorGridWidth *= 2', ''),
        Command('gJ', 'sheet.cursorGridHeight /= 2', ''),
        Command('gK', 'sheet.cursorGridHeight *= 2', ''),

        Command('H', 'sheet.cursorGridWidth -= charGridWidth', ''),
        Command('L', 'sheet.cursorGridWidth += charGridWidth', ''),
        Command('J', 'sheet.cursorGridHeight += charGridHeight', ''),
        Command('K', 'sheet.cursorGridHeight -= charGridHeight', ''),

        Command('zz', 'fixPoint(canvasGridLeft, canvasGridTop, cursorGridLeft, cursorGridTop); sheet.visibleGridWidth=cursorGridWidth; sheet.visibleGridHeight=cursorGridHeight', 'set bounds to cursor'),

        Command('+', 'setZoom(zoomlevel / 1.2); refresh()', 'zoom in 20%'),
        Command('-', 'setZoom(zoomlevel * 1.2); refresh()', 'zoom out 20%'),
        Command('0', 'sheet.gridWidth = 0; sheet.visibleGridWidth = 0; setZoom(1.0); refresh()', 'zoom to fit full extent'),

        # set cursor box with left click
        Command('BUTTON1_PRESSED', 'sheet.cursorGridLeft, sheet.cursorGridTop = gridMouseX, gridMouseY; sheet.cursorGridWidth=0', 'start cursor box with left mouse button press'),
        Command('BUTTON1_RELEASED', 'setCursorSize(gridMouseX, gridMouseY)', 'end cursor box with left mouse button release'),

        Command('BUTTON4_PRESSED', 'tmp=(gridMouseX,gridMouseY); setZoom(zoomlevel/1.2); fixPoint(canvasMouseX, canvasMouseY, *tmp)', 'zoom in with scroll wheel'),
        Command('REPORT_MOUSE_POSITION', 'tmp=(gridMouseX,gridMouseY); setZoom(zoomlevel*1.2); fixPoint(canvasMouseX, canvasMouseY, *tmp)', 'zoom out with scroll wheel'),

        Command('s', 'source.select(list(getRowsInside(*cursorPixelBounds)))', 'select all points within cursor box'),
        Command('t', 'source.unselect(list(getRowsInside(*cursorPixelBounds)))', 'toggle selection of all points within cursor box'),
        Command('u', 'source.unselect(list(getRowsInside(*cursorPixelBounds)))', 'unselect all points within cursor box'),
        Command('gs', 'source.select(list(getRowsInside(*visiblePixelBounds)))', 'select all points visible onscreen'),
        Command('gt', 'source.unselect(list(getRowsInside(*visiblePixelBounds)))', 'toggle selection of all points visible onscreen'),
        Command('gu', 'source.unselect(list(getRowsInside(*visiblePixelBounds)))', 'unselect all points visible onscreen'),
    ]

    def __init__(self, name, *sources, **kwargs):
        super().__init__(name, *sources, **kwargs)

        # bounding box of entire grid in grid units, updated when adding point/line/label or recalcBounds
        self.gridMinX, self.gridMinY = None, None  # derive first bounds on first draw
        self.gridWidth, self.gridHeight = None, None

        # bounding box of visible grid, in grid units
        self.visibleGridLeft = None
        self.visibleGridTop = None
        self.visibleGridWidth = None
        self.visibleGridHeight = None

        # bounding box of cursor (should be contained within visible grid?)
        self.cursorGridLeft, self.cursorGridTop = 0, 0
        self.cursorGridWidth, self.cursorGridHeight = None, None

        self.zoomlevel = 1.0
        self.needsRefresh = False

        # bounding box of gridCanvas, in pixels
        self.gridpoints = []  # list of (grid_x, grid_y, attr, row)
        self.gridlines = []   # list of (grid_x1, grid_y1, grid_x2, grid_y2, attr, row)
        self.gridlabels = []  # list of (grid_x, grid_y, label, attr, row)

    def resetCanvasDimensions(self):
        super().resetCanvasDimensions()
        self.gridCanvasLeft = self.leftMarginPixels
        self.gridCanvasTop = self.topMarginPixels
        self.gridCanvasWidth = self.canvasWidth - self.rightMarginPixels - self.leftMarginPixels
        self.gridCanvasHeight = self.canvasHeight - self.bottomMarginPixels - self.topMarginPixels

    @property
    def statusLine(self):
        gridstr = 'grid (%s,%s)-(%s,%s)' % (self.gridMinX, self.gridMinY, self.gridMaxX, self.gridMaxY)
        vgridstr = 'visibleGrid (%s,%s)-(%s,%s)' % (self.visibleGridLeft, self.visibleGridTop, self.visibleGridRight, self.visibleGridBottom)
        cursorstr = 'cursor (%s,%s)-(%s,%s)' % (self.cursorGridLeft, self.cursorGridTop, self.cursorGridRight, self.cursorGridBottom)
        return ' '.join((gridstr, vgridstr, cursorstr))

    @property
    def canvasMouseX(self):
        return self.mouseX*2

    @property
    def canvasMouseY(self):
        return self.mouseY*4

    @property
    def gridMouseX(self):
        return self.visibleGridLeft + (self.canvasMouseX-self.gridCanvasLeft)*self.visibleGridWidth/self.gridCanvasWidth

    @property
    def gridMouseY(self):
        return self.visibleGridTop + (self.canvasMouseY-self.gridCanvasTop)*self.visibleGridHeight/self.gridCanvasHeight

    def setCursorSize(self, gridX, gridY):
        'sets width based on other side x and y'
        if gridX > self.cursorGridLeft:
            self.cursorGridWidth = max(gridX - self.cursorGridLeft, self.charGridWidth)
        else:
            self.cursorGridWidth = max(self.cursorGridLeft - gridX, self.charGridWidth)
            self.cursorGridLeft = gridX

        if gridY > self.cursorGridTop:
            self.cursorGridHeight = max(gridY - self.cursorGridTop, self.charGridHeight)
        else:
            self.cursorGridHeight = max(self.cursorGridTop - gridY, self.charGridHeight)
            self.cursorGridTop = gridY

    @property
    def charGridWidth(self):
        'Width in grid units of a single char in the terminal'
        return self.visibleGridWidth*2/self.gridCanvasWidth

    @property
    def charGridHeight(self):
        'Height in grid units of a single char in the terminal'
        return self.visibleGridHeight*4/self.gridCanvasHeight

    @property
    def gridMaxX(self):
        return self.gridMinX + self.gridWidth

    @property
    def gridMaxY(self):
        return self.gridMinY + self.gridHeight

    @property
    def cursorGridRight(self):
        return self.cursorGridLeft + self.cursorGridWidth

    @property
    def cursorGridBottom(self):
        return self.cursorGridTop + self.cursorGridHeight

    @property
    def visibleGridRight(self):
        return self.visibleGridLeft + self.visibleGridWidth

    @property
    def visibleGridBottom(self):
        return self.visibleGridTop + self.visibleGridHeight

    @property
    def gridCanvasBottom(self):
        return self.gridCanvasTop + self.gridCanvasHeight

    @property
    def gridCanvasRight(self):
        return self.gridCanvasLeft + self.gridCanvasWidth

    @property
    def visiblePixelBounds(self):
        return [ self.scaleX(self.visibleGridLeft),
                 self.scaleY(self.visibleGridTop),
                 self.scaleX(self.visibleGridLeft+self.visibleGridWidth),
                 self.scaleY(self.visibleGridTop+self.visibleGridHeight)
        ]

    @property
    def cursorPixelBounds(self):
        if self.cursorGridWidth is None:
            return [0,0,0,0]
        return [ self.scaleX(self.cursorGridLeft),
                 self.scaleY(self.cursorGridTop),
                 self.scaleX(self.cursorGridLeft+self.cursorGridWidth),
                 self.scaleY(self.cursorGridTop+self.cursorGridHeight)
        ]

    def point(self, x, y, attr, row=None):
        self.gridpoints.append((x, y, attr, row))

    def line(self, x1, y1, x2, y2, attr, row=None):
        self.gridlines.append((x1, y1, x2, y2, attr, row))

    def label(self, x, y, text, attr, row=None):
        self.gridlabels.append((x, y, text, attr, row))

    def fixPoint(self, canvas_x, canvas_y, grid_x, grid_y):
        'adjust visibleGrid so that (grid_x, grid_y) is plotted at (canvas_x, canvas_y)'
        self.visibleGridLeft = grid_x - self.gridW(canvas_x-self.gridCanvasLeft)
        self.visibleGridTop = grid_y - self.gridH(self.gridCanvasBottom-canvas_y)
        self.refresh()

    def setZoom(self, zoomlevel=None):
        if zoomlevel:
            self.zoomlevel = zoomlevel

        if not self.gridWidth or not self.gridHeight:
            self.gridMinX = min(x for x, y, attr, row in self.gridpoints)
            self.gridWidth = max(x for x, y, attr, row in self.gridpoints) - self.gridMinX
            self.gridMinY = min(y for x, y, attr, row in self.gridpoints)
            self.gridHeight = max(y for x, y, attr, row in self.gridpoints) - self.gridMinY

        if not self.visibleGridWidth or not self.visibleGridHeight:
            self.visibleGridWidth = self.gridWidth*self.zoomlevel
            self.visibleGridHeight = self.gridHeight*self.zoomlevel
            self.visibleGridLeft = self.gridMinX + self.gridWidth/2 - self.visibleGridWidth/2
            self.visibleGridTop = self.gridMinY + self.gridHeight/2 - self.visibleGridHeight/2
        else:
            self.visibleGridWidth = self.gridWidth*self.zoomlevel
            self.visibleGridHeight = self.gridHeight*self.zoomlevel

        if not self.cursorGridWidth or not self.cursorGridHeight:
            self.cursorGridLeft = self.visibleGridLeft
            self.cursorGridTop = self.visibleGridTop
            self.cursorGridWidth = self.charGridWidth
            self.cursorGridHeight = self.charGridHeight

    def checkCursor(self):
        'scroll to make cursor visible'
        return False

    def scaleX(self, x):
        'returns canvas x coordinate'
        return round(self.gridCanvasLeft+(x-self.visibleGridLeft)*self.gridCanvasWidth/self.visibleGridWidth)

    def scaleY(self, y):
        'returns canvas y coordinate'
        return round(self.gridCanvasTop+(y-self.visibleGridTop)*self.gridCanvasHeight/self.visibleGridHeight)

    def gridW(self, canvas_width):
        'canvas X units to grid units'
        return (canvas_width)*self.visibleGridWidth/self.gridCanvasWidth

    def gridH(self, canvas_height):
        'canvas Y units to grid units'
        return (canvas_height)*self.visibleGridHeight/self.gridCanvasHeight

    def refresh(self):
        self.needsRefresh = True

    def plotAll(self):
        self.needsRefresh = False
        self.pixels.clear()
        self.labels.clear()
        self.resetCanvasDimensions()
        for t in self.currentThreads:
            if t.name == 'plotAll_async':
                ctypeAsyncRaise(t, EscapeException)
        self.plotAll_async()

    @async
    def plotAll_async(self):
        'plots points and lines and text onto the PixelCanvas'

        self.setZoom()

        xmin, ymin = self.visibleGridLeft, self.visibleGridTop
        xmax, ymax = self.visibleGridRight, self.visibleGridBottom
        for x, y, attr, row in Progress(self.gridpoints):
            if ymin <= y and y <= ymax:
                if xmin <= x and x <= xmax:
                    self.plotpixel(self.scaleX(x), self.scaleY(y), attr, row)

        for x1, y1, x2, y2, attr, row in Progress(self.gridlines):
            self.plotline(self.scaleX(x1), self.scaleY(y1), self.scaleX(x2), self.scaleY(y2), attr, row)

        for x, y, text, attr, row in Progress(self.gridlabels):
            self.plotlabel(self.scaleX(x), self.scaleY(y), text, attr, row)

