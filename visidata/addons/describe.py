import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet))', 'push describe sheet for all numeric columns')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    return isinstance(col.getDisplayValue(row), (CalcErrorStr, WrongTypeStr))

class DescribeSheet(Sheet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = [
            Column('column', type=str, getter=lambda c: c.name),
            Column('errors',  type=int, getter=lambda c,sheet=self.source: sum(1 for r in sheet.rows if isError(c, r))),
            Column('count',  type=int, getter=lambda c,sheet=self.source: sum(1 for r in sheet.rows if not isNull(c.getValue(r)))),
            Column('distinct',type=int, getter=lambda c,sheet=self.source: len(set(c.values(sheet.rows)))),
            Column('mode',   type=anytype, getter=lambda c,sheet=self.source: statistics.mode(c.values(sheet.rows))),
            Column('min',    type=anytype, getter=lambda c,sheet=self.source: min(c.values(sheet.rows)) if isNumeric(c) else None),
            Column('median', type=anytype, getter=lambda c,sheet=self.source: statistics.median(c.values(sheet.rows)) if isNumeric(c) else None),
            Column('mean',   type=float, getter=lambda c,sheet=self.source: statistics.mean(c.values(sheet.rows)) if isNumeric(c) else None),
            Column('max',    type=anytype, getter=lambda c,sheet=self.source: max(c.values(sheet.rows)) if isNumeric(c) else None),
            Column('stddev', type=float, getter=lambda c,sheet=self.source: statistics.stdev(c.values(sheet.rows)) if isNumeric(c) else None),
        ]

    def reload(self):
        self.rows = self.source.columns
