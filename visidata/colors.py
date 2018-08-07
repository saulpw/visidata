#!/usr/bin/env python3

import curses
from visidata import globalCommand, colors, Sheet, Column, Colorizer, wrapply


globalCommand(None, 'colors', 'vd.push(ColorSheet("vdcolors"))')


class ColorSheet(Sheet):
    rowtype = 'colors'  # rowdef: color number as assigned in the colors object
    columns = [
        Column('color', type=int),
        Column('R', getter=lambda col,row: curses.color_content(curses.pair_number(colors[row])-1)[0]),
        Column('G', getter=lambda col,row: curses.color_content(curses.pair_number(colors[row])-1)[1]),
        Column('B', getter=lambda col,row: curses.color_content(curses.pair_number(colors[row])-1)[2]),
        ]
    colorizers = [
        Colorizer('row', 7, lambda s,c,r,v: r)
    ]

    def reload(self):
        self.rows = sorted(colors.keys(), key=lambda n: wrapply(int, n))
