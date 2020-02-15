from copy import copy

from visidata import Sheet, TsvSheet, options, vd, VisiData


class UsvSheet(TsvSheet):
    pass


@VisiData.api
def save_usv(vd, p, vs):
    usvs = copy(vs)
    usvs.rows = vs.rows
    options.set('delimiter', '\u241e', usvs)
    options.set('row_delimiter', '\u241f', usvs)
    vd.save_tsv(p, usvs)


options.set('delimiter', '\u241e', UsvSheet)  # UsvSheet.options.delimiter='\u241e'
options.set('row_delimiter', '\u241f', UsvSheet)

vd.filetype('usv', UsvSheet)
