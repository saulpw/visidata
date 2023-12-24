from visidata import vd, IndexSheet, VisiData

'Requires visidata/deps/pyxlsb fork'

@VisiData.api
def guess_xls(vd, p):
    if p.open_bytes().read(16).startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
        return dict(filetype='xlsb', _likelihood=10)


@VisiData.api
def open_xlsb(vd, p):
    return XlsbIndex(p.base_stem, source=p)


class XlsbIndex(IndexSheet):
    def iterload(self):
        vd.importExternal('pyxlsb', '-e git+https://github.com/saulpw/pyxlsb.git@visidata#egg=pyxlsb')
        from pyxlsb import open_workbook

        wb = open_workbook(str(self.source))
        for name in wb.sheets:
            yield wb.get_sheet(name, True)
