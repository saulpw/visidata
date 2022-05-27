from copy import copy

from visidata import Sheet, TsvSheet, options, vd, VisiData

@VisiData.api
def open_usv(vd, p):
    vs = TsvSheet(p.name, source=p)
    vs.options.delimiter = '\u241f'
    vs.options.row_delimiter = '\u241e'
    return vs

@VisiData.api
def save_usv(vd, p, vs):
    usvs = copy(vs)
    usvs.rows = vs.rows
    usvs.options.delimiter = '\u241f'
    usvs.options.row_delimiter = '\u241e'
    vd.save_tsv(p, usvs)
