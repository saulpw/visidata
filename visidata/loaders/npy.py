from visidata import VisiData, vd, Sheet, date, anytype, options, Column, Progress, ColumnItem, vlen, PyobjSheet, currency, floatlocale, TypedWrapper

'Loaders for .npy and .npz.  Save to .npy.  Depends on the zip loader.'

@VisiData.api
def open_npy(vd, p):
    return NpySheet(p.name, source=p)

@VisiData.api
def open_npz(vd, p):
    return NpzSheet(p.name, source=p)

vd.option('npy_allow_pickle', False, 'numpy allow unpickling objects (unsafe)')

class NpySheet(Sheet):
    def iterload(self):
        import numpy
        if not hasattr(self, 'npy'):
            self.npy = numpy.load(str(self.source), encoding='bytes', **self.options.getall('npy_'))
        self.reloadCols()
        yield from Progress(self.npy, total=len(self.npy))

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


class NpzSheet(vd.ZipSheet):
    # rowdef: tuple(tablename, table)
    columns = [
        ColumnItem('name', 0),
        ColumnItem('length', 1, type=vlen),
    ]

    def iterload(self):
        import numpy
        self.npz = numpy.load(str(self.source), encoding='bytes')
        yield from Progress(self.npz.items())

    def openRow(self, row):
        import numpy
        tablename, tbl = row
        if isinstance(tbl, numpy.ndarray):
            return NpySheet(tablename, npy=tbl)

        return PyobjSheet(tablename, source=tbl)


@VisiData.api
def save_npy(vd, p, sheet):
    import numpy as np

    dtype = []

    for col in Progress(sheet.visibleCols):
        if col.type in (int, vlen):
            dt = 'i8'
        elif col.type in (float, currency, floatlocale):
            dt = 'f8'
        elif col.type is date:
            dt = 'datetime64[s]'

        else: #  if col.type in (str, anytype):
            width = col.getMaxWidth(sheet.rows)
            dt = 'U'+str(width)
        dtype.append((col.name, dt))

    data = []
    for typedvals in sheet.iterdispvals(format=False):
        nprow = []
        for col, val in typedvals.items():
            if isinstance(val, TypedWrapper):
                if col.type is anytype:
                    val = ''
                else:
                    val = options.safe_error
            elif col.type is date:
                val = np.datetime64(val.isoformat())
            nprow.append(val)
        data.append(tuple(nprow))

    arr = np.array(data, dtype=dtype)
    with p.open_bytes(mode='w') as outf:
        np.save(outf, arr, **sheet.options.getall('npy_'))
