from visidata import *

unit_leftx = 0
unit_rightx = 10.0
unit_topy = 1.5
unit_bottomy = -1.5

globalCommand('m', 'vd.push(makeGraph(rows, keyCols and keyCols[0], cursorCol))', 'graph the current column vs the first key column (or row number)')
globalCommand('gm', 'vd.push(makeGraph(rows, keyCols and keyCols[0], *numericCols(nonKeyVisibleCols)))', 'graph all numeric columns vs the first key column (or row number)')

graphColors = 'green red yellow blue cyan magenta'.split()

def numericCols(cols):
    # isNumeric from describe.py
    return [c for c in cols if isNumeric(c)]

def datapoints(xcol, ycol, rows, color):
    attr = colors[color]
    if xcol:
        return list((xcol.getTypedValue(row), ycol.getTypedValue(row), attr) for row in rows)
    else:
        return list((x, ycol.getTypedValue(row), attr) for x, row in enumerate(rows))

def makeGraph(rows, xcol, *ycols):
    vs = BrailleCanvasSheet('graph', rows, xcol, *ycols)
    vs.vd = vd()
    return vs

class BrailleCanvasSheet(Sheet):
    columns=[Column('foo')]
    def __init__(self, name, *sources, **kwargs):
        super().__init__(name, *sources, **kwargs)
        self.labels = []

    def pixel_to_unit_x(self, pix_x):
        return unit_leftx+pix_x*self.scale_x

    def pixel_to_unit_y(self, pix_y):
        return (unit_bottomy+pix_y*self.scale_y)

    @property
    def scale_x(self):
        'number of units per horizontal pixel'
        return (unit_rightx - unit_leftx)/(vd().windowWidth*2)

    @property
    def scale_y(self):
        'number of units per vertical pixel'
        return (unit_topy - unit_bottomy)/(self.nVisibleRows*4)

    def draw(self, scr):
        pixels = collections.defaultdict(dict) # [y][x]
        for unit_x, unit_y, color in self.rows:
            pix_x = round((unit_x-unit_leftx)/self.scale_x)
            pix_y = round((unit_topy-unit_y)/self.scale_y)
            pixels[pix_y][pix_x] = color

        scr.erase()
        for y in range(0, self.nVisibleRows+1):
            for x in range(0, vd().windowWidth):
                block_colors = [
                    pixels[y*4  ].get(x*2, None),
                    pixels[y*4+1].get(x*2, None),
                    pixels[y*4+2].get(x*2, None),
                    pixels[y*4  ].get(x*2+1, None),
                    pixels[y*4+1].get(x*2+1, None),
                    pixels[y*4+2].get(x*2+1, None),
                    pixels[y*4+3].get(x*2, None),
                    pixels[y*4+3].get(x*2+1, None)
                ]
                pow2 = 1
                braille_num = 0
                for c in block_colors:
                    if c:
                        braille_num += pow2
                    pow2 *= 2

                only_colors = list(c for c in block_colors if c)
                if only_colors:
                    colormode = collections.Counter(only_colors).most_common(1)[0][0]
                    scr.addstr(y, x, chr(0x2800+braille_num), colormode)
                else:
                    assert braille_num == 0

        for unit_x, unit_y, txt, colorname in self.labels:
            xpos = round((unit_x-unit_leftx)/(self.scale_x*2))
            ypos = round((unit_topy-unit_y)/(self.scale_y*4))
            if ypos >= 0 and ypos <= self.nVisibleRows:
                clipdraw(scr, ypos, xpos, txt, colors[colorname], len(txt))
            else:
                status(ypos, xpos, txt, colorname)

    def plot(self, unit_x, unit_y, color):
        self.addRow((unit_x, unit_y, color))

    def label(self, unit_x, unit_y, txt, color):
        self.labels.append((unit_x, unit_y, txt, color))

    def legend(self, i, txt, color):
        self.label(self.pixel_to_unit_x(vd().windowWidth*2-30), self.pixel_to_unit_y((i+1)*4), txt, color)

    def setbounds(self):
        global unit_leftx, unit_topy, unit_rightx, unit_bottomy
        unit_leftx = min(x for x,y,c in self.rows)
        unit_rightx = max(x for x,y,c in self.rows)
        unit_topy = max(y for x,y,c in self.rows)
        unit_bottomy = min(y for x,y,c in self.rows)
        unit_leftx -= (unit_rightx-unit_leftx)*.05
        unit_rightx += (unit_rightx-unit_leftx)*.05
        unit_topy += (unit_topy-unit_bottomy)*.05
        unit_bottomy -= (unit_topy-unit_bottomy)*.05

    @async
    def reload(self):
        self.rows = []
        self.labels = []

        rows = self.sources[0]
        xcol = self.sources[1]
        ycols = self.sources[2:]
        for i, ycol in enumerate(ycols):
            dp = datapoints(xcol, ycol, rows, graphColors[i])
            self.rows.extend(list(dp))

        self.setbounds()

        for i, ycol in enumerate(ycols):
            self.legend(i, ycol.name, graphColors[i])

        yrange = unit_topy-unit_bottomy
        yincr = yrange/self.nVisibleRows  # vd().windowHeight
        ndigits = len(str(int(yincr)))
        yincr = int(round(yincr, -ndigits))
        yval = int(round(unit_bottomy, -ndigits))

        self.label(unit_leftx, unit_bottomy, str(int(unit_bottomy)), 'white')
        for i in range(0, self.nVisibleRows):
            ytop = self.pixel_to_unit_y(i*4+3)
            self.label(unit_leftx, ytop, str(int(ytop)), "white")


