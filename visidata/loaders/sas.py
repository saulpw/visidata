import logging

from visidata import VisiData, Sheet, Progress, ColumnItem, anytype, vd

SASTypes = {
    'string': str,
    'number': float,
}

@VisiData.api
def open_xpt(vd, p):
    return XptSheet(p.base_stem, source=p)

@VisiData.api
def open_sas7bdat(vd, p):
    return SasSheet(p.base_stem, source=p)

class XptSheet(Sheet):
    def iterload(self):
        xport = vd.importExternal('xport')
        xport.v56 = vd.importExternal('xport.v56', 'xport>=3')
        with open(self.source, 'rb') as fp:
            self.library = xport.v56.load(fp)

            self.columns = []
            dataset = self.library[list(self.library.keys())[0]]

            varnames = dataset.contents.Variable.values
            types = dataset.contents.Type.values

            for i, (varname, typestr) in enumerate(zip(varnames, types)):
                self.addColumn(ColumnItem(varname, i, type=float if typestr == 'Numeric' else str))

            for row in dataset.values:
                yield list(row)


class SasSheet(Sheet):
    def iterload(self):
        sas7bdat = vd.importExternal('sas7bdat')
        self.dat = sas7bdat.SAS7BDAT(str(self.source), skip_header=True, log_level=logging.CRITICAL)
        self.columns = []
        for col in self.dat.columns:
            self.addColumn(ColumnItem(col.name.decode('utf-8'), col.col_id, type=SASTypes.get(col.type, anytype)))

        with self.dat as fp:
            yield from Progress(fp, total=self.dat.properties.row_count)
