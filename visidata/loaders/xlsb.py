from visidata import vd, IndexSheet, VisiData

'Requires visidata/deps/pyxlsb fork'


@VisiData.api
def open_xlsb(vd, p):
    return XlsbIndex(p.name, source=p)

class XlsbIndex(IndexSheet):
    def iterload(self):
        from pyxlsb import open_workbook

        wb = open_workbook(str(self.source))
        for name in wb.sheets:
            yield wb.get_sheet(name, True)
