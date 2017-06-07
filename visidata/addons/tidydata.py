from visidata import *

command('M', 'vd.push(MeltedSheet(sheet))', 'push melted (unpivoted) sheet')

option('melt_var_colname', 'Variable', 'column name to use for the melted variable name')
option('melt_value_colname', 'Value', 'column name to use for the melted value')

class MeltedSheet(Sheet):
    """Perform "melt", the reverse of "pivot", on input sheet."""
    def __init__(self, sheet):
        super().__init__(sheet.name + '_melted', sheet)

    @async
    def reload(self):
        sheet = self.source
        self.columns = [SubrowColumn(c, 0) for c in sheet.keyCols]
        self.nKeys = sheet.nKeys
        self.columns.extend([Column(options.melt_var_colname, getter=lambda r: r[1].name),
                             Column(options.melt_value_colname, getter=lambda r: r[1].getValue(r[0]))])

        colsToMelt = [c.copy() for c in sheet.nonKeyVisibleCols]

        self.rows = []
        self.progressMade = 0
        self.progressTotal = len(self.source.rows)
        for r in self.source.rows:
            for c in colsToMelt:
                if c.getValue(r) is not None:
                    self.rows.append((r, c))
            self.progressMade += 1
