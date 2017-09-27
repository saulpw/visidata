import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet))', 'open Describe Sheet')

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

def values(c):
    return c.getValues(c.sheet.rows)

class DescribeSheet(Sheet):
    columns = [
            Column('column', type=str, getter=lambda r: r.name),
            SourceColumn('errors',  type=len, getter=lambda sheet,r: tuple(sr for sr in sheet.rows if isError(r, sr))),
            SourceColumn('nulls',  type=len, getter=lambda sheet,r: tuple(sr for sr in sheet.rows if isNull(r.getValue(sr)))),
            SourceColumn('distinct',type=len, getter=lambda sheet,r: set(values(r))),
            SourceColumn('mode',   type=anytype, getter=lambda sheet,r: statistics.mode(values(r))),
            SourceColumn('min',    type=anytype, getter=lambda sheet,r: min(values(r)) if isNumeric(r) else None),
            SourceColumn('median', type=anytype, getter=lambda sheet,r: statistics.median(values(r)) if isNumeric(r) else None),
            SourceColumn('mean',   type=float, getter=lambda sheet,r: statistics.mean(values(r)) if isNumeric(r) else None),
            SourceColumn('max',    type=anytype, getter=lambda sheet,r: max(values(r)) if isNumeric(r) else None),
            SourceColumn('stddev', type=float, getter=lambda sheet,r: statistics.stdev(values(r)) if isNumeric(r) else None),
    ]
    commands = [
        Command('zs', 'source.select(cursorCell)', 'select rows on source sheet which are being described in current cell'),
        Command('zu', 'source.unselect(cursorCell)', 'unselect rows on source sheet which are being described in current cell'),
        Command('z'+ENTER, 'vs=copy(source); vs.rows=cursorValue; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)', 'open copy of source sheet with rows described in current cell'),
        Command(ENTER, 'vd.push(SheetFreqTable(source, cursorRow))', 'open a Frequency Table sheet grouped on column referenced in current row')
    ]

    @async
    def reload(self):
        self.rows = self.source.columns  # allow for column deleting/reordering
