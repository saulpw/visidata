from visidata import *

command("g'", 'vd.push(StaticCopy(sheet))', 'evaluate all cells and copy to new sheet (freeze)')

class StaticCopy(Sheet):
    """Duplicate source sheet, allowing updating to proceed off-screen."""
    def __init__(self, source):
        super().__init__(source.name + "'", source)

        self.columns = [ColumnItem(col.name, i, width=col.width, type=col.type) for i,col in enumerate(self.source.columns)]

    @async
    def reload(self):
        self.rows = []
        for r in self.genProgress(self.source.rows):
            self.rows.append([col.getValue(r) for col in self.source.columns])
