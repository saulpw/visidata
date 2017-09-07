import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet))', 'push describe sheet for all numeric columns')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    return hasattr(col.getCell(row), 'error')

def isNull(v):
    return isNullFunc()(v)


class SourceColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, cache=True, **kwargs)

    def getValue(self, row):
        return self.getter(self.sheet.source, row)


class DescribeSheet(Sheet):
    columns = [
            Column('column', type=str, getter=lambda r: r[0].name),
            SourceColumn('errors',  type=len, getter=lambda sheet,r: tuple(sr for sr in sheet.rows if isError(r[0], sr))),
            SourceColumn('nulls',  type=len, getter=lambda sheet,r: tuple(sr for sr in sheet.rows if isNull(r[0].getValue(sr)))),
            SourceColumn('distinct',type=len, getter=lambda sheet,r: set(r[1])),
            SourceColumn('mode',   type=anytype, getter=lambda sheet,r: statistics.mode(r[1])),
            SourceColumn('min',    type=anytype, getter=lambda sheet,r: min(r[1]) if isNumeric(r[0]) else None),
            SourceColumn('median', type=anytype, getter=lambda sheet,r: statistics.median(r[1]) if isNumeric(r[0]) else None),
            SourceColumn('mean',   type=float, getter=lambda sheet,r: statistics.mean(r[1]) if isNumeric(r[0]) else None),
            SourceColumn('max',    type=anytype, getter=lambda sheet,r: max(r[1]) if isNumeric(r[0]) else None),
            SourceColumn('stddev', type=float, getter=lambda sheet,r: statistics.stdev(r[1]) if isNumeric(r[0]) else None),
    ]
    commands = [
        Command('zs', 'source.select(cursorCell)', 'select rows in this cell on source sheet'),
        Command('zu', 'source.unselect(cursorCell)', 'unselect rows in this cell on source sheet'),
        Command('z^J', 'vs=copy(source); vs.rows=cursorCell; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)', 'unselect rows in this cell on source sheet')
    ]

    @async
    def reload(self):
        self.rows = []
        for c in self.genProgress(self.source.columns):
            self.addRow((c, c.values(self.source.rows)))
