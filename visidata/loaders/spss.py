from visidata import VisiData, Sheet, Progress, asyncthread, ItemColumn, vd


@VisiData.api
def open_spss(vd, p):
    return SpssSheet(p.base_stem, source=p)
VisiData.open_sav = VisiData.open_spss


class SpssSheet(Sheet):
    def loader(self):
        savReaderWriter = vd.importExternal('savReaderWriter')
        self.rdr = savReaderWriter.SavReader(str(self.source))
        with self.rdr as reader:
            self.columns = []
            for i, vname in enumerate(reader.varNames):
                vtype = float if reader.varTypes[vname] == 0 else str
                self.addColumn(ItemColumn(vname.decode('utf-8'), i, type=vtype))

            self.rows = []
            for r in Progress(reader, total=reader.shape.nrows):
                self.addRow(r)
