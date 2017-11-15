import statistics

from visidata import *

globalCommand('I', 'vd.push(DescribeSheet(sheet.name+"_describe", sheet, sourceRows=selectedRows or rows))', 'open Describe Sheet')

def isNumeric(col):
    return col.type in (int,float,currency,date)

def isError(col, row):
    try:
        v = col.getValue(row)
        if v is not None:
            col.type(v)
        return False
    except EscapeException:
        raise
    except Exception as e:
        return True

def returnException(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except EscapeException:
        raise
    except Exception as e:
        return e


class DescribeColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, getter=lambda col,srccol: col.sheet.describeData[srccol].get(col.name), **kwargs)

# rowdef: Column from source sheet
class DescribeSheet(Sheet):
    columns = [
            Column('column', type=str, getter=lambda col,row: row.name),
            DescribeColumn('errors', type=len),
            DescribeColumn('nulls',  type=len),
            DescribeColumn('distinct',type=len),
            DescribeColumn('mode',   type=anytype),
            DescribeColumn('min',    type=anytype),
            DescribeColumn('median', type=anytype),
            DescribeColumn('mean',   type=float),
            DescribeColumn('max',    type=anytype),
            DescribeColumn('stddev', type=float),
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
        self.describeData = { col: {} for col in self.source.columns }

        for srccol in Progress(self.source.columns):
            d = self.describeData[srccol]
            isNull = isNullFunc()

            vals = list()
            d['errors'] = list()
            d['nulls'] = list()
            d['distinct'] = set()
            for sr in self.sourceRows:
                try:
                    v = srccol.getValue(sr)
                    if isNull(v):
                        d['nulls'].append(sr)
                    else:
                        v = srccol.type(v)
                        vals.append(v)
                    d['distinct'].add(v)
                except EscapeException:
                    raise
                except Exception as e:
                    d['errors'].append(e)

            d['mode'] = returnException(statistics.mode, vals)
            if isNumeric(srccol):
                d['min'] = min(vals)
                d['median'] = statistics.median(vals)
                d['mean'] = statistics.mean(vals)
                d['max'] = max(vals)
                d['stddev'] = statistics.stdev(vals)

