from visidata import *

option('color_graph_axis', 'white', 'color for graph axis labels')
option('show_graph_labels', True, 'show axes and legend on graph')

left_margin_chars = 10
right_margin_chars = 6
bottom_margin_chars = 1  # reserve bottom line for x axis

globalCommand('m', 'vd.push(GraphSheet(sheet.name+"_graph", selectedRows or rows, keyCols and keyCols[0] or None, cursorCol))', 'graph the current column vs the first key column (or row number)')
globalCommand('gm', 'vd.push(GraphSheet(sheet.name+"_graph", selectedRows or rows, keyCols and keyCols[0], *numericCols(nonKeyVisibleCols)))', 'graph all numeric columns vs the first key column (or row number)')

graphColors = 'green red yellow cyan magenta white 38 136 168'.split()

def numericCols(cols):
    # isNumeric from describe.py
    return [c for c in cols if isNumeric(c)]

# pixels covering whole real terminal
#   (0,0) in upper left
class BrailleCanvas(Sheet):
    columns=[Column('')]  # to eliminate errors outside of draw()

    def __init__(self, name, *sources, **kwargs):
        super().__init__(name, *sources, **kwargs)
        self.pixels = collections.defaultdict(dict) # [y][x] = colorname
        self.labels = []  # (pix_x, pix_y, text, colorname)

    @property
    def pixel_width(self):
        return vd().windowWidth*2

    @property
    def pixel_height(self):
        return (vd().windowHeight-2)*4

    def set_pixel(self, pix_x, pix_y, colorname):
        self.pixels[pix_y][pix_x] = colors[colorname]

    def line(self, x1, y1, x2, y2, colorname):
        'Draws coords of the line from (x1, y1) to (x2, y2)'
        xdiff = max(x1, x2) - min(x1, x2)
        ydiff = max(y1, y2) - min(y1, y2)
        xdir = 1 if x1 <= x2 else -1
        ydir = 1 if y1 <= y2 else -1

        r = max(xdiff, ydiff)

        for i in range(r+1):
            x = x1
            y = y1

            if r:
                y += ydir * (i * ydiff) / r
                x += xdir * (i * xdiff) / r

            self.set_pixel(x, y, colorname)

    def label(self, pix_x, pix_y, txt, colorname):
        self.labels.append((pix_x, pix_y, txt, colors[colorname]))

    def draw(self, scr):
        if not self.pixels:
            self.refresh()
        scr.erase()
        for y in range(0, self.nVisibleRows+1):
            for x in range(0, vd().windowWidth):
                block_colors = [
                    self.pixels[y*4  ].get(x*2, None),
                    self.pixels[y*4+1].get(x*2, None),
                    self.pixels[y*4+2].get(x*2, None),
                    self.pixels[y*4  ].get(x*2+1, None),
                    self.pixels[y*4+1].get(x*2+1, None),
                    self.pixels[y*4+2].get(x*2+1, None),
                    self.pixels[y*4+3].get(x*2, None),
                    self.pixels[y*4+3].get(x*2+1, None)
                ]
                pow2 = 1
                braille_num = 0
                for c in block_colors:
                    if c:
                        braille_num += pow2
                    pow2 *= 2

                if braille_num != 0:
                    only_colors = list(c for c in block_colors if c)
                    colormode = collections.Counter(only_colors).most_common(1)[0][0]
                    scr.addstr(y, x, chr(0x2800+braille_num), colormode)

        if options.show_graph_labels:
            for pix_x, pix_y, txt, attr in self.labels:
                clipdraw(scr, int(pix_y/4), int(pix_x/2), txt, attr, len(txt))


# provides unit->pixel conversion, axis labels, legend
class GraphSheet(BrailleCanvas):
    commands=[
        Command('^L', 'refresh()', 'redraw all pixels on canvas'),
        Command('w', 'options.show_graph_labels = not options.show_graph_labels', 'toggle show_graph_labels')
    ]
    def __init__(self, name, rows, xcol, *ycols, **kwargs):
        super().__init__(name, rows, **kwargs)
        self.xcol = xcol
        self.ycols = ycols
        if xcol:
            isNumeric(self.xcol) or error('%s type is non-numeric' % xcol.name)
        for col in ycols:
            isNumeric(col) or error('%s type is non-numeric' % col.name)
        self.unit_leftx = None
        self.unit_rightx = None
        self.unit_topy = None
        self.unit_bottomy = None
        self.set_bounds()

    def set_bounds(self):
        self.pix_leftx = left_margin_chars*2
        self.pix_rightx = self.pixel_width-right_margin_chars*2
        self.pix_topy = 0
        self.pix_bottomy = self.pixel_height-bottom_margin_chars*4

    @async
    def refresh(self):
        'plot all points, scaled to the canvas'
        self.set_bounds()
        self.create_labels()
        self.pixels.clear()
        scale_x = (self.unit_rightx-self.unit_leftx)/(self.pix_rightx-self.pix_leftx)
        scale_y = (self.unit_topy-self.unit_bottomy)/(self.pix_bottomy-self.pix_topy)
        for unit_x, unit_y, color in self.genProgress(self.rows):
            pix_x = self.pix_leftx + (unit_x-self.unit_leftx)/scale_x
            pix_y = self.pix_topy + (self.unit_topy-unit_y)/scale_y  # invert y axis
            self.pixels[round(pix_y)][round(pix_x)] = color

    def legend(self, i, txt, colorname):
        self.label(self.pix_rightx-30, self.pix_topy+i*4, txt, colorname)

    def plot(self, x, y, attr):
        if self.unit_leftx is None or x < self.unit_leftx:     self.unit_leftx = x
        if self.unit_rightx is None or x > self.unit_rightx:   self.unit_rightx = x
        if self.unit_bottomy is None or y < self.unit_bottomy: self.unit_bottomy = y
        if self.unit_topy is None or y > self.unit_topy:       self.unit_topy = y

        self.addRow((x, y, attr))

    @async
    def reload(self):
#        rows = self.sources[0]

        self.rows = []
        nerrors = 0
        nplotted = 0
        for i, ycol in enumerate(self.ycols):
            colorname = graphColors[i % len(graphColors)]
            attr = colors[colorname]

            for rownum, row in enumerate(self.genProgress(self.source)):
                try:
                    unit_x = self.xcol.getTypedValue(row) if self.xcol else rownum
                    unit_y = ycol.getTypedValue(row)
                    self.plot(unit_x, unit_y, attr)
                    nplotted += 1
                except Exception:
                    nerrors += 1

        status('plotting %d points (%d errors)' % (nplotted, nerrors))
        self.refresh()

    def add_y_axis_label(self, frac):
        amt = self.unit_bottomy + frac*(self.unit_topy-self.unit_bottomy)
        if isinstance(self.unit_bottomy, int):
            txt = '%d' % amt
        elif isinstance(self.unit_bottomy, float):
            txt = '%.02f' % amt
        else:
            txt = str(frac)
        self.label(0, (1.0-frac)*self.pix_bottomy, txt, options.color_graph_axis)

    def add_x_axis_label(self, frac):
        amt = self.unit_leftx + frac*(self.unit_rightx-self.unit_leftx)
        if isinstance(self.unit_leftx, int):
            txt = '%d' % round(amt)
        elif isinstance(self.unit_leftx, float):
            txt = '%.02f' % amt
        else:
            txt = str(frac)

        self.label(self.pix_leftx+frac*(self.pix_rightx-self.pix_leftx), self.pix_bottomy+4, txt, options.color_graph_axis)

    def create_labels(self):
        self.labels = []

        # y-axis
        self.add_y_axis_label(1.00)
        self.add_y_axis_label(0.75)
        self.add_y_axis_label(0.50)
        self.add_y_axis_label(0.25)
        self.add_y_axis_label(0.00)

        # x-axis
        self.add_x_axis_label(1.00)
        self.add_x_axis_label(0.75)
        self.add_x_axis_label(0.50)
        self.add_x_axis_label(0.25)
        self.add_x_axis_label(0.00)

        xname = self.xcol.name if self.xcol else 'row#'
        self.label(0, self.pix_bottomy+4, '%*s»' % (left_margin_chars-2, xname), options.color_graph_axis)

        for i, ycol in enumerate(self.ycols):
            colorname = graphColors[i]
            self.legend(i, ycol.name, colorname)
