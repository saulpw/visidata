from visidata import vd, VisiData, TsvSheet


@VisiData.api
def open_usv(vd, p):
    p.options.set('delimiter', '\u241f', p, cmdlog=False)
    p.options.set('row_delimiter', '\u241e', p, cmdlog=False)
    return UsvSheet(p.base_stem, source=p)


class UsvSheet(TsvSheet):
    pass


@VisiData.api
def save_usv(vd, p, vs):
    p.options.set('delimiter', '\u241f', p, cmdlog=False)
    p.options.set('row_delimiter', '\u241e', p, cmdlog=False)
    vd.save_tsv(p, vs)
