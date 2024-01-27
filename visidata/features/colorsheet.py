import curses
from visidata import VisiData, colors, Sheet, Column, ItemColumn, RowColorizer, wrapply, BaseSheet


class ColorSheet(Sheet):
    rowtype = 'colors'  # rowdef: [fg, bg, color_attr, colornamestr]
    columns = [
        ItemColumn('fg', 0, type=int),
        ItemColumn('bg', 1, type=int),
        ItemColumn('pairnum', 2),
        ItemColumn('name', 3),
    ]
    colorizers = [
        RowColorizer(7, None, lambda s,c,r,v: r and r[3])
    ]

    def iterload(self):
        self.rows = []
        for k, v in colors.color_pairs.items():
            fg, bg = k
            pairnum, colorname = v
            yield [fg, bg, pairnum, colorname]

        for i in range(0, 256):
            yield [i, 0, None, f'{i}']

    def draw(self, scr):
        super().draw(scr)
        rightcol = max(self._visibleColLayout.values())
        xstart = rightcol[0] + rightcol[1] + 4
        for i, r in enumerate(self.rows[(self.topRowIndex//6)*6:(self.bottomRowIndex//6+1)*6]):
            fg, bg, _, colorstr = r
            s = f'█▌{fg:3}▐█'
            y=i//6+1
            x=(i%6)*(len(s)+2)+xstart
            if y > self.windowHeight-1:
                break
            if r is self.cursorRow:
                s = f'█[{fg:3}]█'
            scr.addstr(y, x, s, colors[colorstr].attr)


BaseSheet.addCommand(None, 'open-colors', 'vd.push(vd.colorsSheet)', 'open Color Sheet with available terminal colors')

@VisiData.lazy_property
def colorsSheet(vd):
    return ColorSheet('colors')
