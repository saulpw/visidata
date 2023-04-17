import curses
from visidata import VisiData, colors, Sheet, Column, RowColorizer, wrapply, BaseSheet


class ColorSheet(Sheet):
    rowtype = 'colors'  # rowdef: [(fg,bg), (color_attr, colornamestr)]
    columns = [
        Column('color', getter=lambda c,r: r[1][1]),
        Column('fg', type=int, getter=lambda c,r: r[0][0]),
        Column('bg', type=int, getter=lambda c,r: r[0][1]),
        Column('attr', width=0, type=int, getter=lambda c,r: r[1][0]),
        ]
    colorizers = [
        RowColorizer(7, None, lambda s,c,r,v: r and r[1][1])
    ]

    def iterload(self):
        self.rows = []
        for k, v in colors.color_pairs.items():
            yield [k, v]

        for i in range(0, 256):
            yield [(i, 0), (None, f'{i}')]

    def draw(self, scr):
        super().draw(scr)
        rightcol = max(self._visibleColLayout.values())
        xstart = rightcol[0] + rightcol[1] + 4
        for i, r in enumerate(self.rows[(self.topRowIndex//6)*6:(self.bottomRowIndex//6+1)*6]):
            y=i//6+1
            x=(i%6)*3+xstart
            c = r[1][1]
            s = '██'
            if y > self.windowHeight-1:
                break
            if r is self.cursorRow:
                x -= 1
                s = '[██]'
            scr.addstr(y, x, s, colors[c])


BaseSheet.addCommand(None, 'open-colors', 'vd.push(vd.colorsSheet)', 'open Color Sheet with available terminal colors')

@VisiData.lazy_property
def colorsSheet(vd):
    return ColorSheet()
