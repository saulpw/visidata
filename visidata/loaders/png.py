from visidata import *

def open_png(p):
    return PNGSheet(p.name, source=p)

@functools.lru_cache(256)
def rgb_to_attr(r,g,b,a):
    if a == 0: return 0
    if r > g and r > b: return colors['red']
    if g > r and g > b: return colors['green']
    if b > r and b > g: return colors['blue']
    if a == 255: return colors['white']
    return 0

class PNGSheet(Sheet):
    rowtype = 'pixels'  # rowdef: tuple(x, y, r, g, b, a)
    columns = [ColumnItem(name, i, type=int) for i, name in enumerate('x y R G B A'.split())] + [
        Column('attr', type=int, getter=lambda col,row: rgb_to_attr(*row[2:]))
    ]
    nKeys = 2
    def newRow(self):
        return list((None, None, 0, 0, 0, 0))

    def iterload(self):
        import png
        r = png.Reader(bytes=self.source.read_bytes())
        self.width, self.height, pixels, md = r.asRGBA()
        for y, row in enumerate(pixels):
            for i in range(0, len(row)-1, 4):
                r,g,b,a = row[i:i+4]
                yield [i//4, y, r, g, b, a]


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


@VisiData.api
def save_png(vd, p, vs):
    if isinstance(vs, Canvas):
        return save_png(p, vs.source)

    palette = collections.OrderedDict()
    palette[(0,0,0,0)] = 0   # invisible black is 0

    pixels = list([0]*vs.width for y in range(vs.height))

    for x,y,r,g,b,a in Progress(sorted(vs.rows), 'saving'):
        color = tuple((r,g,b,a))
        colornum = palette.get(color, None)
        if colornum is None:
            colornum = palette[color] = len(palette)
        pixels[y][x] = colornum

    vd.status('saving %sx%sx%s' % (vs.width, vs.height, len(palette)))

    import png
    with open(p, 'wb') as fp:
        w = png.Writer(vs.width, vs.height, palette=list(palette.keys()))
        w.write(fp, pixels)

    vd.status('saved')

PNGSheet.addCommand('.', 'plot-sheet', 'vd.push(PNGDrawing(name+"_plot", source=sheet, sourceRows=rows))', 'plot this png')
