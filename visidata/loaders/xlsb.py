from visidata import vd, IndexSheet

'Requires visidata/deps/pyxlsb fork'


class XlsbIndex(IndexSheet):
    def iterload(self):
        from pyxlsb import open_workbook

        wb = open_workbook(str(self.source))
        for name in wb.sheets:
            vs = wb.get_sheet(name, True)
            vs.reload()
            yield vs


vd.filetype('xlsb', XlsbIndex)
