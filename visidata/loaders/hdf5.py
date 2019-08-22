from visidata import *

class SheetH5Obj(Sheet):
    'Support sheets in HDF5 format.'
    def reload(self):
        import h5py
        if isinstance(self.source, h5py.Group):
            self.rowtype = 'sheets'
            self.columns = [
                Column(self.source.name, type=str, getter=lambda col,row: row.source.name.split('/')[-1]),
                Column('type', type=str, getter=lambda col,row: type(row.source).__name__),
                Column('nItems', type=int, getter=lambda col,row: len(row.source)),
            ]
            self.rows = []
            for k, v in self.source.items():
                subname = joinSheetnames(self.name, k)
                self.addRow(SheetH5Obj(subname, source=v))
        elif isinstance(self.source, h5py.Dataset):
            if len(self.source.shape) == 1:
                self.columns = [ColumnItem(colname, colname) for colname in self.source.dtype.names or [0]]
                self.rows = self.source[:]  # copy
            elif len(self.source.shape) == 2:  # matrix
                ncols = self.source.shape[1]
                self.columns = [ColumnItem('', i, width=8) for i in range(ncols)]
                self.rows = self.source[:]  # copy
            else:
                status('too many dimensions in shape %s' % str(self.source.shape))
        else:
            status('unknown h5 object type %s' % type(self.source))
        self.recalc()

SheetH5Obj.addCommand(ENTER, 'dive-row', 'vd.push(cursorRow)')
SheetH5Obj.addCommand('A', 'dive-metadata', 'vd.push(SheetDict(cursorRow.name + "_attrs", source=cursorRow.attrs))')

class open_hdf5(SheetH5Obj):
    def __init__(self, p):
        import h5py
        super().__init__(p.name, source=h5py.File(str(p), 'r'))

open_h5 = open_hdf5
