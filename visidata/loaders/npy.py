from visidata import *


def open_npy(p):
    return NumpySheet(p.name, source=p)


class NumpySheet(Sheet):
    @asyncthread
    def reload(self):
        import numpy
        self.rows = numpy.load(self.source.resolve(), encoding='bytes')
        self.columns = []

        for i, (name, fmt) in enumerate(self.rows.dtype.descr):
            self.addColumn(ColumnItem(name, i))
