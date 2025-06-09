from visidata import VisiData, TsvSheet


@VisiData.api
def open_psv(vd, p):
    return PsvSheet(p.name, source=p)


class PsvSheet(TsvSheet):
    pass


PsvSheet.options.delimiter = '|'
