import copy

from visidata import TsvSheet, options, save_tsv

__all__ = ['open_usv', 'save_usv', 'UsvSheet']

def open_usv(p):
    return UsvSheet(p.name, source=p)

class UsvSheet(TsvSheet):
    pass


def save_usv(p, vs):
    usvs = copy.copy(vs)
    usvs.rows = vs.rows
    options.set('delimiter', '\u241e', usvs)
    options.set('row_delimiter', '\u241f', usvs)
    save_tsv(p, vs)


options.set('delimiter', '\u241e', UsvSheet)  # UsvSheet.options.delimiter='\u241e'
options.set('row_delimiter', '\u241f', UsvSheet)
