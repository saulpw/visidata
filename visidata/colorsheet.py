import curses
from visidata import globalCommand, colors, Sheet, Column, RowColorizer, wrapply


class ColorSheet(Sheet):
    rowtype = 'colors'  # rowdef: color number as assigned in the colors object
    columns = [
        Column('color', getter=lambda c,r: r[1][1]),
        Column('fg', type=int, getter=lambda c,r: r[0][0]),
        Column('bg', type=int, getter=lambda c,r: r[0][1]),
        Column('attr', width=0, type=int, getter=lambda c,r: r[1][0]),
        ]
    colorizers = [
        RowColorizer(7, None, lambda s,c,r,v: r and r[1][1])
    ]

    def reload(self):
        self.rows = list(colors.color_pairs.items())


globalCommand(None, 'colors', 'vd.push(ColorSheet("vdcolors"))', 'open Color Sheet with an overview of curses colors and codes')
