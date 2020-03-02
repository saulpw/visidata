from copy import copy

from visidata import Sheet, TsvSheet, options, vd, VisiData


class UsvSheet(TsvSheet):
    pass


@VisiData.api
def save_usv(vd, p, vs):
    usvs = copy(vs)
    usvs.rows = vs.rows
    usvs.options.delimiter = '\u241e'
    usvs.options.row_delimiter = '\u241f'
    vd.save_tsv(p, usvs)


UsvSheet.options.delimiter = '\u241e'
UsvSheet.options.row_delimiter = '\u241f'

vd.filetype('usv', UsvSheet)
