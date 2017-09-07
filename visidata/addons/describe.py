import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet))', 'push describe sheet for all numeric columns')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    return hasattr(col.getDisplay(row), 'error')

def isNull(v):
    return isNullFunc()(v)

class SourceColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def _getValue(self, row):
        return self.getter(self.sheet.source, row)

class DescribeSheet(Sheet):
    columns = [
            Column('column', type=str, getter=lambda c: c.name),
            SourceColumn('errors',  type=len, getter=lambda sheet,c: tuple(r for r in sheet.rows if isError(c, r))),
            SourceColumn('nulls',  type=len, getter=lambda sheet,c: tuple(r for r in sheet.rows if isNull(c.getValue(r)))),
            SourceColumn('distinct',type=len, getter=lambda sheet,c: set(c.values(sheet.rows))),
            SourceColumn('mode',   type=anytype, getter=lambda sheet,c: statistics.mode(c.values(sheet.rows))),
            SourceColumn('min',    type=anytype, getter=lambda sheet,c: min(c.values(sheet.rows)) if isNumeric(c) else None),
            SourceColumn('median', type=anytype, getter=lambda sheet,c: statistics.median(c.values(sheet.rows)) if isNumeric(c) else None),
            SourceColumn('mean',   type=float, getter=lambda sheet,c: statistics.mean(c.values(sheet.rows)) if isNumeric(c) else None),
            SourceColumn('max',    type=anytype, getter=lambda sheet,c: max(c.values(sheet.rows)) if isNumeric(c) else None),
            SourceColumn('stddev', type=float, getter=lambda sheet,c: statistics.stdev(c.values(sheet.rows)) if isNumeric(c) else None),
    ]
    commands = [
        Command('zs', 'source.select(cursorCell)', 'select rows in this cell on source sheet'),
        Command('zu', 'source.unselect(cursorCell)', 'unselect rows in this cell on source sheet'),
        Command('z^J', 'vs=copy(source); vs.rows=cursorCell; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)', 'unselect rows in this cell on source sheet')
    ]

    def reload(self):
        self.rows = self.source.columns
