from visidata import *

def open_spss(p):
    return SpssSheet(p.name, source=p)
open_sav = open_spss


class SpssSheet(Sheet):
    @asyncthread
    def reload(self):
        import savReaderWriter
        self.rdr = savReaderWriter.SavReader(self.source.resolve())
        with self.rdr as reader:
            self.columns = []
            for i, vname in enumerate(reader.varNames):
                vtype = float if reader.varTypes[vname] == 0 else str
                self.addColumn(ColumnItem(vname.decode('utf-8'), i, type=vtype))

            self.rows = []
            for r in Progress(reader, total=reader.shape.nrows):
                self.rows.append(r)

