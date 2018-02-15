from visidata import *


@functools.lru_cache(256)
def rgb_to_attr(r,g,b,a):
    if a == 0: return 0
    if r > g and r > b: return colors['red']
    if g > r and g > b: return colors['green']
    if b > r and b > g: return colors['blue']
    if a == 255: return colors['white']
    return 0


def open_png(p):
    return PNGSheet(p.name, source=p)


# rowdef: tuple(x, y, r, g, b, a)
class PNGSheet(Sheet):
    columns = [ColumnItem(name, i, type=int) for i, name in enumerate('x y R G B A'.split())] + [
        Column('attr', type=int, getter=lambda col,row: rgb_to_attr(*row[2:]))
    ]
    nKeys = 2
    commands = [
        Command('.', 'vd.push(PNGDrawing(name+"_plot", source=sheet, sourceRows=rows))', 'plot this png', 'plot-png')
    ]
    def newRow(self):
        return list((None, None, 0, 0, 0, 0))

    @async
    def reload(self):
        import png
        r = png.Reader(bytes=self.source.read_bytes())
        self.width, self.height, pixels, md = r.asRGBA()
        self.rows = []
        for y, row in enumerate(pixels):
            for i in range(0, len(row)-1, 4):
                r,g,b,a = row[i:i+4]
                self.addRow([i//4, y, r, g, b, a])


class PNGDrawing(Plotter):
    commands = [
        Command('.', 'vd.push(source)', 'push table of pixels for this png'),
        Command('move-left', 'sheet.cursorX -= 1', ''),
        Command('move-right', 'sheet.cursorX += 1', ''),
        Command('move-up', 'sheet.cursorY -= 1', ''),
        Command('move-down', 'sheet.cursorY += 1', ''),
        Command('move-top', 'sheet.cursorY = 0', ''),
        Command('move-bottom', 'sheet.cursorY = plotheight/4-1', ''),
        Command('move-far-left', 'sheet.cursorX = 0', ''),
        Command('move-far-right', 'sheet.cursorX = plotwidth/2-1', ''),
        Command('0', 'setPixel(rowsWithin(Box(cursorX*2, cursorY*4, 1, 3)), 0)', ''),
        Command('1', 'togglePixel(rowsWithin(Box(cursorX*2, cursorY*4, 0, 0)))', ''),
        Command('2', 'togglePixel(rowsWithin(Box(cursorX*2, cursorY*4+1, 0, 0)))', ''),
        Command('3', 'togglePixel(rowsWithin(Box(cursorX*2, cursorY*4+2, 0, 0)))', ''),
        Command('4', 'togglePixel(rowsWithin(Box(cursorX*2+1, cursorY*4, 0, 0)))', ''),
        Command('5', 'togglePixel(rowsWithin(Box(cursorX*2+1, cursorY*4+1, 0, 0)))', ''),
        Command('6', 'togglePixel(rowsWithin(Box(cursorX*2+1, cursorY*4+2, 0, 0)))', ''),
        Command('7', 'togglePixel(rowsWithin(Box(cursorX*2, cursorY*4+3, 0, 0)))', ''),
        Command('8', 'togglePixel(rowsWithin(Box(cursorX*2+1, cursorY*4+3, 0, 0)))', ''),
        Command('9', 'setPixel(rowsWithin(Box(cursorX*2, cursorY*4, 1, 3)), 255)', ''),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursorX = self.cursorY = 0

    def togglePixel(self, rows):
        for row in rows:
            x,y,r,g,b,a = row
            self.pixels[y][x][rgb_to_attr(r,g,b,a)].remove(row)
            row[5] = a = 0 if row[5] else 255
            self.plotpixel(x, y, rgb_to_attr(r,g,b,a), row)

    def setPixel(self, rows, attr):
        for row in rows:
            x,y,r,g,b,a = row
            self.pixels[y][x][rgb_to_attr(r,g,b,a)].remove(row)
            row[5] = a = attr
            self.plotpixel(x, y, rgb_to_attr(r,g,b,a), row)

    @property
    def plotterCursorBox(self):
        return Box(self.cursorX*2, self.cursorY*4, 2, 4)

    @async
    def reload(self):
        self.resetCanvasDimensions()
        for row in self.sourceRows:
            x, y, r, g, b, a = row
            self.plotpixel(x, y, rgb_to_attr(r,g,b,a), row)

@async
def save_png(vs, fn):
    if isinstance(vs, PNGSheet):
        pass
    elif isinstance(vs, PNGDrawing):
        vs = vs.source
    else:
        error('sheet must be from png loader (for now)')

    palette = collections.OrderedDict()
    palette[(0,0,0,0)] = 0   # invisible black is 0

    pixels = list([0]*vs.width for y in range(vs.height))

    for x,y,r,g,b,a in Progress(sorted(vs.rows)):
        color = tuple((r,g,b,a))
        colornum = palette.get(color, None)
        if colornum is None:
            colornum = palette[color] = len(palette)
        pixels[y][x] = colornum

    status('saving %sx%sx%s' % (vs.width, vs.height, len(palette)))

    import png
    with open(fn, 'wb') as fp:
        w = png.Writer(vs.width, vs.height, palette=list(palette.keys()))
        w.write(fp, pixels)

    status('saved')
