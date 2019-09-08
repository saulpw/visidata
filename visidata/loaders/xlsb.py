from visidata import vd, asyncthread, IndexSheet

'Requires visidata/deps/pyxlsb fork'

def open_xlsb(p):
    return XlsbIndex(p.name, source=p)


class XlsbIndex(IndexSheet):
    @asyncthread
    def reload(self):
        from pyxlsb import open_workbook

        wb = open_workbook(str(self.source))
        for name in wb.sheets:
            vs = wb.get_sheet(name, True)
            vs.reload()
            self.addRow(vs)
