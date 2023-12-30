from visidata import VisiData, vd, Sheet, Path, Column, ItemColumn, BaseSheet

@VisiData.api
def open_h5(vd, p):
    return Hdf5ObjSheet(p.base_stem, source=p)

VisiData.open_hdf5 = VisiData.open_h5

class Hdf5ObjSheet(Sheet):
    'Support sheets in HDF5 format.'
    def iterload(self):
        h5py = vd.importExternal('h5py')
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
                if source.dtype.names:
                    for i, colname in enumerate(source.dtype.names):
                        self.addColumn(ItemColumn(colname, colname), index=i)
                    yield from source  # copy
                else:
                    self.addColumn(ItemColumn(source.name, 0))
                    for v in source:
                        yield [v]
            elif len(source.shape) == 2:  # matrix
                ncols = source.shape[1]
                for i in range(ncols):
                    self.addColumn(ItemColumn('', i, width=8), index=i)
                self.recalc()
                yield from source  # copy
            else:
                vd.fail('too many dimensions in shape %s' % str(source.shape))
        else:
            vd.fail('unknown h5 object type %s' % type(source))


    def openRow(self, row):
        h5py = vd.importExternal('h5py')
        if isinstance(row, BaseSheet):
            return row
        if isinstance(row, h5py.HLObject):
            return Hdf5ObjSheet(row)

        numpy = vd.importExternal('numpy')
        from .npy import NpySheet
        if isinstance(row, numpy.ndarray):
            return NpySheet(None, npy=row)


Hdf5ObjSheet.addCommand('A', 'dive-metadata', 'vd.push(SheetDict(cursorRow.name + "_attrs", source=cursorRow.attrs))', 'open metadata sheet for object referenced in current row')
