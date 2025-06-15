from visidata import VisiData, vd, Sheet, date, anytype, options, Column, ItemColumn, Progress, vlen, PyobjSheet, TypedWrapper
from itertools import chain

'Loaders for .npy and .npz.  Save to .npy.  Depends on the zip loader.'

@VisiData.api
def open_npy(vd, p):
    return NpySheet(p.base_stem, source=p)

@VisiData.api
def open_npz(vd, p):
    return NpzSheet(p.base_stem, source=p)

vd.option('npy_allow_pickle', False, 'numpy allow unpickling objects (unsafe)')
vd.option('npy_matrix_enumerate', False, 'enumerate matrix rows and columns')

class NpySheet(Sheet):
    def iterload(self):
        numpy = vd.importExternal('numpy')
        if not hasattr(self, 'npy'):
            self.npy = numpy.load(str(self.source), encoding='bytes', allow_pickle=bool(self.options.npy_allow_pickle))
        self.reloadCols()
        transpose = len(self.npy.shape)==1 and not bool(self.npy.dtype.names)
        if transpose:
            source = self.npy[:,None]
        else:
            source = self.npy

        nrows = len(self.npy)

        if self.options.npy_matrix_enumerate:
            source = list(list((chain((i,), row))) for i, row in enumerate(source))

        yield from Progress(source, nrows)


    def reloadCols(self):
        self.columns = []
        if len(self.npy.shape)==1:
            for i, (colname, fmt, *shape) in enumerate(self.npy.dtype.descr):
                if not colname:
                    colname = f"col{i}"
                ctype = _guess_type(shape, fmt)
                if ctype=="time":
                    self.addColumn(Column(colname, type=date, getter=lambda c,r,i=i: str(r[i])))
                    continue
                self.addColumn(ItemColumn(colname, i, type=ctype))
        elif len(self.npy.shape)==2:
            ncols = self.npy.shape[1]
            ctype = _guess_type(None, self.npy.dtype.descr[0][1])

            if self.options.npy_matrix_enumerate:
                self.addColumn(ItemColumn("row", 0, width=8, keycol=1, type=int), index=0)
                for i in range(ncols):
                    self.addColumn(ItemColumn(f'col{i}', i+1, width=8, type=ctype), index=i+1)
            else:
                for i in range(ncols):
                    self.addColumn(ItemColumn('', i, width=8, type=ctype), index=i)
        else:
            vd.fail(f"too many dimensions in shape {self.npy.shape}")

def _guess_type(shape, fmt):
    if shape:
        return anytype
    elif 'M' in fmt:
        return "time"
    elif 'i' in fmt or 'u' in fmt:
        return int
    elif 'f' in fmt:
        return float
    return anytype

class NpzSheet(vd.ZipSheet):
    # rowdef: tuple(tablename, table)
    columns = [
        ItemColumn('name', 0),
        ItemColumn('length', 1, type=vlen),
    ]

    def iterload(self):
        numpy = vd.importExternal('numpy')
        self.npz = numpy.load(str(self.source), encoding='bytes', allow_pickle=bool(self.options.npy_allow_pickle))
        yield from Progress(self.npz.items())

    def openRow(self, row):
        numpy = vd.importExternal('numpy')
        tablename, tbl = row
        if isinstance(tbl, numpy.ndarray):
            return NpySheet(tablename, npy=tbl)

        return PyobjSheet(tablename, source=tbl)


@VisiData.api
def save_npy(vd, p, sheet):
    np = vd.importExternal('numpy')

    dtype = []

    for col in Progress(sheet.visibleCols):
        if col.type in (int, vlen):
            dt = 'i8'
        elif col.type is date:
            dt = 'datetime64[s]'
        elif col.type in vd.numericTypes:
            dt = 'f8'
        else: #  if col.type in (str, anytype):
            width = col.getMaxDataWidth(sheet.rows)
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
        np.save(outf, arr, allow_pickle=bool(sheet.options.npy_allow_pickle))
