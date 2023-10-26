import os

from visidata import vd, Sheet, VisiData, FreqTableSheet, BaseSheet, asyncthread, CellColorizer

vd.options.disp_menu_fmt = '|  VisiData {vd.version} | {vd.motd}'

Sheet.addCommand('', 'addcol-source', 'source.addColumn(copy(cursorCol))', 'add copy of current column to source sheet')  #988  frosencrantz
