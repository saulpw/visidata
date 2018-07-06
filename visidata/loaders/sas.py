from visidata import *
import logging

SASTypes = {
    'string': str,
    'number': float,
}


def open_xpt(p):
    return XptSheet(p.name, source=p)

def open_sas7bdat(p):
    return SasSheet(p.name, source=p)


class XptSheet(Sheet):
    @asyncthread
    def reload(self):
        import xport
        with open(self.source.resolve(), 'rb') as fp:
            self.rdr = xport.Reader(fp)

            self.columns = []
            for i, var in enumerate(self.rdr._variables):
                self.addColumn(ColumnItem(var.name, i, type=float if var.numeric else str))

            self.rows = []
            for row in self.rdr:
                self.rows.append(row)


class SasSheet(Sheet):
    @asyncthread
    def reload(self):
        import sas7bdat
        self.dat = sas7bdat.SAS7BDAT(self.source.resolve(), skip_header=True, log_level=logging.CRITICAL)
        self.columns = []
        for col in self.dat.columns:
            self.addColumn(ColumnItem(col.name.decode('utf-8'), col.col_id, type=SASTypes.get(col.type, anytype)))

        with self.dat as fp:
            self.rows = []
            for row in Progress(fp, total=self.dat.properties.row_count):
                self.rows.append(row)
