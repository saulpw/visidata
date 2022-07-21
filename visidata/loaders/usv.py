from copy import copy

from visidata import Sheet, TsvSheet, options, vd, VisiData

@VisiData.api
def open_usv(vd, p):
    return TsvSheet(p.name, source=p, delimiter='\u241f', row_delimiter='\u241e')

@VisiData.api
def save_usv(vd, p, vs):
    vd.save_tsv(p, vs, row_delimiter='\u241e', delimiter='\u241f')
