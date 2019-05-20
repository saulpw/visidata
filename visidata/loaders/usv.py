import copy

from visidata import TsvSheet, options, save_tsv

def open_usv(p):
    return UsvSheet(p.name, source=p)

class UsvSheet(TsvSheet):
    pass


def save_usv(p, vs):
    usvs = copy.copy(vs)
    usvs.rows = vs.rows
    options.set('tsv_delimiter', '\u241e', usvs)
    options.set('tsv_row_delimiter', '\u241f', usvs)
    save_tsv(p, vs)


options.set('tsv_delimiter', '\u241e', UsvSheet)  # UsvSheet.options.tsv_delimiter='\u241e'
options.set('tsv_row_delimiter', '\u241f', UsvSheet)
