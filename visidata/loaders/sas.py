from visidata import *
import logging

SASTypes = {
    'string': str,
    'number': float,
}


class XptSheet(Sheet):
    def iterload(self):
        import xport
        with open(self.source, 'rb') as fp:
            self.rdr = xport.Reader(fp)

            self.columns = []
            for i, var in enumerate(self.rdr._variables):
                self.addColumn(ColumnItem(var.name, i, type=float if var.numeric else str))

            yield from self.rdr


class SasSheet(Sheet):
    def iterload(self):
        import sas7bdat
        self.dat = sas7bdat.SAS7BDAT(str(self.source), skip_header=True, log_level=logging.CRITICAL)
        self.columns = []
        for col in self.dat.columns:
            self.addColumn(ColumnItem(col.name.decode('utf-8'), col.col_id, type=SASTypes.get(col.type, anytype)))

        with self.dat as fp:
            yield from Progress(fp, total=self.dat.properties.row_count)


vd.filetype('xpt', XptSheet)
vd.filetype('sas7bdat', SasSheet)
