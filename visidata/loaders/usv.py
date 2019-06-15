import copy

from visidata import Sheet, TsvSheet, options

__all__ = ['open_usv', 'UsvSheet']

def open_usv(p):
    return UsvSheet(p.name, source=p)

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
