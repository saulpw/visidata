from visidata import *


def open_npy(p):
    return NumpySheet(p.name, source=p)


class NumpySheet(Sheet):
    @asyncthread
    def reload(self):
        import numpy

        self.npy = numpy.load(self.source.resolve(), encoding='bytes')
        self.columns = []

        for i, (name, fmt) in enumerate(self.npy.dtype.descr):
            if 'M' in fmt:
                self.addColumn(Column(name, type=date, getter=lambda c,r,i=i: str(r[i])))
                continue
            elif 'i' in fmt:
                t = int
            elif 'f' in fmt:
                t = float
            else:
                t = anytype
            self.addColumn(ColumnItem(name, i, type=t))

        self.rows = []
        for row in Progress(self.npy):
            self.addRow(row)


@asyncthread
def save_npy(p, sheet):
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
            if col.type is date:
                nprow.append(np.datetime64(col.getTypedValue(row).isoformat()))
            else:
                nprow.append(col.getTypedValue(row))
        data.append(tuple(nprow))

    arr = np.array(data, dtype=dtype)
    with p.open_bytes(mode='w') as outf:
        np.save(outf, arr, allow_pickle=False)
