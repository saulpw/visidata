from statistics import mode, median, mean, stdev

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", source=sheet, sourceRows=selectedRows or rows))', 'open Describe Sheet')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    try:
        v = col.getValue(row)
        if v is not None:
            col.type(v)
        return False
    except Exception as e:
        return True

def returnException(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except Exception as e:
        return e


class DescribeColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, getter=lambda col,srccol: col.sheet.describeData[srccol].get(col.name), **kwargs)

# rowdef: Column from source sheet
class DescribeSheet(Sheet):
    rowtype = 'columns'
    columns = [
            Column('column', type=str, getter=lambda col,row: row.name),
            DescribeColumn('errors', type=len),
            DescribeColumn('nulls',  type=len),
            DescribeColumn('distinct',type=len),
            DescribeColumn('mode',   type=anytype),
            DescribeColumn('min',    type=anytype),
            DescribeColumn('max',    type=anytype),
            DescribeColumn('median', type=anytype),
            DescribeColumn('mean',   type=float),
            DescribeColumn('stdev',  type=float),
    ]
    commands = [
        Command('zs', 'source.select(cursorValue)', 'select rows on source sheet which are being described in current cell'),
        Command('zu', 'source.unselect(cursorValue)', 'unselect rows on source sheet which are being described in current cell'),
        Command('z'+ENTER, 'vs=copy(source); vs.rows=cursorValue; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)', 'open copy of source sheet with rows described in current cell'),
        Command(ENTER, 'vd.push(SheetFreqTable(source, cursorRow))', 'open a Frequency Table sheet grouped on column referenced in current row'),
        Command('!', 'source.toggleKeyColumn(source.columns.index(cursorRow))', 'pin current column on left as a key column on source sheet')
    ]
    colorizers = [
        Colorizer('row', 7, lambda self,c,r,v: options.color_key_col if r in self.source.keyCols else None),
    ]

    @async
    def reload(self):
        self.rows = list(self.source.columns)  # column deleting/reordering here does not affect actual columns
        self.describeData = { col: {} for col in self.source.columns }

        for srccol in Progress(self.source.columns):
            self.reloadColumn(srccol)

    @async
    def reloadColumn(self, srccol):
            d = self.describeData[srccol]
            isNull = isNullFunc()

            vals = list()
            d['errors'] = list()
            d['nulls'] = list()
            d['distinct'] = set()
            for sr in Progress(self.sourceRows):
                try:
                    v = srccol.getValue(sr)
                    if isNull(v):
                        d['nulls'].append(sr)
                    else:
                        v = srccol.type(v)
                        vals.append(v)
                    d['distinct'].add(v)
                except Exception as e:
                    d['errors'].append(sr)

            d['mode'] = self.calcStatistic(d, mode, vals)
            if isNumeric(srccol):
                for func in [min, max, median, mean, stdev]:
                    d[func.__name__] = self.calcStatistic(d, func, vals)

    def calcStatistic(self, d, func, *args, **kwargs):
        r = returnException(func, *args, **kwargs)
        d[func.__name__] = r
        return r
