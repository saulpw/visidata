from visidata import *


def open_npy(p):
    return NpySheet(p.name, source=p)


def open_npz(p):
    return NpzSheet(p)


class NumpySheet(Sheet):
    def reload(self):
        self.reloadCols()

        self.rows = []
        for row in Progress(self.npy):
            self.addRow(row)

    def reloadCols(self):
        self.columns = []
        for i, (name, fmt, *shape) in enumerate(self.npy.dtype.descr):
            if shape:
                t = anytype
            elif 'M' in fmt:
                self.addColumn(Column(name, type=date, getter=lambda c,r,i=i: str(r[i])))
                continue
            elif 'i' in fmt:
                t = int
            elif 'f' in fmt:
                t = float
            else:
                t = anytype
            self.addColumn(ColumnItem(name, i, type=t))


class NpySheet(NumpySheet):
    @asyncthread
    def reload(self):
        import numpy
        self.npy = numpy.load(str(self.source), encoding='bytes')
        super().reload()



class NpzSheet(ArchiveSheet):
    # rowdef = (tablename, table)
    columns = [
        ColumnItem('name', 0),
        ColumnItem('length', 1, type=vlen),
    ]
    @asyncthread
    def reload(self):
        import numpy
        self.npz = numpy.load(str(self.source), encoding='bytes')
        self.rows = list(self.npz.items())

    def getInnerSheet(self, row):
        import numpy
        tablename, tbl = row
        if isinstance(tbl, numpy.ndarray):
            return NumpySheet(tablename, npy=tbl)

        return load_pyobj(tablename, tbl)

@Sheet.api
def save_npy(sheet, p):
    import numpy as np

    dtype = []

    for col in Progress(sheet.visibleCols):
        if col.type in (int, vlen):
            dt = 'i8'
        elif col.type in (float, currency):
            dt = 'f8'
        elif col.type is date:
            dt = 'datetime64[s]'

        else: #  if col.type in (str, anytype):
            width = col.getMaxWidth(sheet.rows)
            dt = 'U'+str(width)
        dtype.append((col.name, dt))

    data = []
    for row in Progress(sheet.rows):
        nprow = []
        for col in sheet.visibleCols:
            val = col.getTypedValue(row)
            if isinstance(val, TypedWrapper):
                if col.type is anytype:
                    val = ''
                else:
                    val = col.type()
            elif col.type is date:
                val = np.datetime64(val.isoformat())
            nprow.append(val)
        data.append(tuple(nprow))

    arr = np.array(data, dtype=dtype)
    with p.open_bytes(mode='w') as outf:
        np.save(outf, arr, allow_pickle=False)


NpzSheet.addCommand(None, 'dive-row', 'vd.push(getInnerSheet(cursorRow))')
