from visidata import *


globalCommand('T', 'vd.push(TransposeSheet(name+"_T", source=sheet))', 'open new sheet with rows and columns transposed', 'data-transpose')


# rowdef: Column
class TransposeSheet(Sheet):
    @async
    def reload(self):
        # key rows become column names
        self.columns = [
            Column('_'.join(c.name for c in self.source.keyCols),
                   getter=lambda c,origcol: origcol.name)
        ]
        self.keyCols = self.columns[:]

        # rows become columns
        for row in Progress(self.source.rows):
            self.addColumn(Column('_'.join(self.source.rowkey(row)),
                                  getter=lambda c,origcol,row=row: origcol.getValue(row)))

        # columns become rows
        self.rows = list(self.source.nonKeyVisibleCols)
