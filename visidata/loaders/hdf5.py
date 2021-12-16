from visidata import VisiData, vd, Sheet, Path, Column, ColumnItem, BaseSheet

@VisiData.api
def open_h5(vd, p):
    return Hdf5ObjSheet(p.name, source=p)

VisiData.open_hdf5 = VisiData.open_h5

class Hdf5ObjSheet(Sheet):
    'Support sheets in HDF5 format.'
    def iterload(self):
        import h5py
        source = self.source
        if isinstance(self.source, Path):
            source = h5py.File(str(self.source), 'r')

        self.columns = []
        if isinstance(source, h5py.Group):
            self.rowtype = 'sheets'
            self.columns = [
                Column(source.name, type=str, getter=lambda col,row: row.source.name.split('/')[-1], keycol=1),
                Column('type', type=str, getter=lambda col,row: type(row.source).__name__),
                Column('nItems', type=int, getter=lambda col,row: len(row.source)),
            ]
            self.recalc()
            for k, v in source.items():
                yield Hdf5ObjSheet(self.name, k, source=v)
        elif isinstance(source, h5py.Dataset):
            if len(source.shape) == 1:
                for i, colname in enumerate(source.dtype.names or [0]):
                    self.addColumn(ColumnItem(colname, colname), index=i)
                yield from source  # copy
            elif len(source.shape) == 2:  # matrix
                ncols = source.shape[1]
                for i in range(ncols):
                    self.addColumn(ColumnItem('', i, width=8), index=i)
                self.recalc()
                yield from source  # copy
            else:
                vd.status('too many dimensions in shape %s' % str(source.shape))
        else:
            vd.status('unknown h5 object type %s' % type(source))


    def openRow(self, row):
        import h5py
        if isinstance(row, BaseSheet):
            return row
        if isinstance(row, h5py.HLObject):
            return Hdf5ObjSheet(row)

        import numpy
        from .npy import NpySheet
        if isinstance(row, numpy.ndarray):
            return NpySheet(None, npy=row)


Hdf5ObjSheet.addCommand('A', 'dive-metadata', 'vd.push(SheetDict(cursorRow.name + "_attrs", source=cursorRow.attrs))', 'open metadata sheet for object referenced in current row')
