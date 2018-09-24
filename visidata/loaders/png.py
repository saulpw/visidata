from visidata import *


@functools.lru_cache(256)
def rgb_to_attr(r,g,b,a):
    if a == 0: return 0
    if r > g and r > b: return colors['red'].attr
    if g > r and g > b: return colors['green'].attr
    if b > r and b > g: return colors['blue'].attr
    if a == 255: return colors['white'].attr
    return 0


def open_png(p):
    return PNGSheet(p.name, source=p)


class PNGSheet(Sheet):
    rowtype = 'pixels'  # rowdef: tuple(x, y, r, g, b, a)
    columns = [ColumnItem(name, i, type=int) for i, name in enumerate('x y R G B A'.split())] + [
        Column('attr', type=int, getter=lambda col,row: rgb_to_attr(*row[2:]))
    ]
    nKeys = 2
    def newRow(self):
        return list((None, None, 0, 0, 0, 0))

    @asyncthread
    def reload(self):
        import png
        r = png.Reader(bytes=self.source.read_bytes())
        self.width, self.height, pixels, md = r.asRGBA()
        self.rows = []
        for y, row in enumerate(pixels):
            for i in range(0, len(row)-1, 4):
                r,g,b,a = row[i:i+4]
                self.addRow([i//4, y, r, g, b, a])

class PNGDrawing(Canvas):
    aspectRatio = 1.0
    rowtype = 'pixels'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    @asyncthread
    def reload(self):
        self.reset()
        for row in self.sourceRows:
            x, y, r, g, b, a = row
            self.point(x, y, rgb_to_attr(r,g,b,a), row)
        self.refresh()

PNGSheet.addCommand('.', 'plot-sheet', 'vd.push(PNGDrawing(name+"_plot", source=sheet, sourceRows=rows))')
PNGDrawing.addCommand('.', 'dive-source', 'vd.push(source)')

@asyncthread
def save_png(p, vs):
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
    with open(p.resolve(), 'wb') as fp:
        w = png.Writer(vs.width, vs.height, palette=list(palette.keys()))
        w.write(fp, pixels)

    status('saved')
