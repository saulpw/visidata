import copy

from visidata import Sheet, TsvSheet, options, vd


class UsvSheet(TsvSheet):
    pass


@Sheet.api
def save_usv(vs, p):
    usvs = copy.copy(vs)
    usvs.rows = vs.rows
    options.set('delimiter', '\u241e', usvs)
    options.set('row_delimiter', '\u241f', usvs)
    usvs.save_tsv(p)


options.set('delimiter', '\u241e', UsvSheet)  # UsvSheet.options.delimiter='\u241e'
options.set('row_delimiter', '\u241f', UsvSheet)

vd.filetype('usv', UsvSheet)
