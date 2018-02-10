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


class PNGSheet(Sheet):
    commands = [
        Command('.', 'vd.push(PNGDrawing(name+"_plot", source=sheet))', 'plot this png')
    ]
    @async
    def reload(self):
        import png
        r = png.Reader(bytes=self.source.read_bytes())
        self.width, self.height, pixels, md = r.asRGBA()
        self.rows = list(pixels)
        self.columns = []
        for x in range(0, self.width*4, 4):
            self.addColumn(ColumnItem('R%s' % (x//4), x, width=4))
            self.addColumn(ColumnItem('G%s' % (x//4), x+1, width=4))
            self.addColumn(ColumnItem('B%s' % (x//4), x+2, width=4))
            self.addColumn(ColumnItem('A%s' % (x//4), x+3, width=4))


class PNGDrawing(Plotter):
    commands = [
        Command('.', 'vd.push(source)', 'push table of pixels for this png')
    ]
    @async
    def reload(self):
        x_factor = self.plotwidth/self.source.width
        y_factor = self.plotheight/self.source.height
        x_factor = y_factor = min(x_factor, y_factor)
        for y, row in enumerate(self.source.rows):
            for i in range(0, len(row)-1, 4):
                x = i//4
                r,g,b,a = row[i:i+4]
                attr = rgb_to_attr(r,g,b,a)
                if attr != 0:
                    self.plotpixel(x, y, attr)
