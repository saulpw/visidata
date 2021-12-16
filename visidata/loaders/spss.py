from visidata import VisiData, Sheet, Progress, asyncthread, ColumnItem


@VisiData.api
def open_spss(vd, p):
    return SpssSheet(p.name, source=p)
VisiData.open_sav = VisiData.open_spss


class SpssSheet(Sheet):
    @asyncthread
    def reload(self):
        import savReaderWriter
        self.rdr = savReaderWriter.SavReader(str(self.source))
        with self.rdr as reader:
            self.columns = []
            for i, vname in enumerate(reader.varNames):
                vtype = float if reader.varTypes[vname] == 0 else str
                self.addColumn(ColumnItem(vname.decode('utf-8'), i, type=vtype))

            self.rows = []
            for r in Progress(reader, total=reader.shape.nrows):
                self.addRow(r)
