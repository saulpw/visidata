from visidata import vd, VisiData, TsvSheet


@VisiData.api
def open_psv(vd, p):
    p.options.set('delimiter', '|', p, cmdlog=False)
    return PsvSheet(p.base_stem, source=p)


class PsvSheet(TsvSheet):
    pass


@VisiData.api
def save_psv(vd, p, vs):
    p.options.set('delimiter', '|', p, cmdlog=False)
    vd.save_tsv(p, vs)
