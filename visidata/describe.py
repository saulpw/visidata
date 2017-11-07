import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet))', 'open Describe Sheet')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    return hasattr(col.getCell(row), 'error')

def isNull(v):
    return isNullFunc()(v)

def values(c):
    return c.getValues(c.sheet.rows)

# rowdef: Column from source sheet
class DescribeSheet(Sheet):
    columns = [
            Column('column', type=str, getter=lambda col,row: row.name),
            Column('errors', cache=True, type=len, getter=lambda col,row: tuple(sr for sr in col.sheet.source.rows if isError(row, sr))),
            Column('nulls',  cache=True, type=len, getter=lambda col,row: tuple(sr for sr in col.sheet.source.rows if isNull(row.getValue(sr)))),
            Column('distinct',cache=True, type=len, getter=lambda col,row: set(values(row))),
            Column('mode',   cache=True, type=anytype, getter=lambda col,row: statistics.mode(values(row))),
            Column('min',    cache=True, type=anytype, getter=lambda col,row: min(values(row)) if isNumeric(row) else None),
            Column('median', cache=True, type=anytype, getter=lambda col,row: statistics.median(values(row)) if isNumeric(row) else None),
            Column('mean',   cache=True, type=float, getter=lambda col,row: statistics.mean(values(row)) if isNumeric(row) else None),
            Column('max',    cache=True, type=anytype, getter=lambda col,row: max(values(row)) if isNumeric(row) else None),
            Column('stddev', cache=True, type=float, getter=lambda col,row: statistics.stdev(values(row)) if isNumeric(row) else None),
    ]
    commands = [
        Command('zs', 'source.select(cursorValue)', 'select rows on source sheet which are being described in current cell'),
        Command('zu', 'source.unselect(cursorValue)', 'unselect rows on source sheet which are being described in current cell'),
        Command('z'+ENTER, 'vs=copy(source); vs.rows=cursorValue; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)', 'open copy of source sheet with rows described in current cell'),
        Command(ENTER, 'vd.push(SheetFreqTable(source, cursorRow))', 'open a Frequency Table sheet grouped on column referenced in current row')
    ]

    @async
    def reload(self):
        self.rows = self.source.columns  # allow for column deleting/reordering
