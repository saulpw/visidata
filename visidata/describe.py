from statistics import mode, median, mean, stdev

from visidata import *

max_threads = 2

Sheet.addCommand('I', 'describe-sheet', 'vd.push(DescribeSheet(sheet.name+"_describe", source=[sheet]))')
globalCommand('gI', 'describe-all', 'vd.push(DescribeSheet("describe_all", source=vd.sheets))')

def isError(col, row):
    try:
        v = col.getValue(row)
        if v is not None:
            col.type(v)
        return False
    except Exception as e:
        return True


class DescribeColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, getter=lambda col,srccol: col.sheet.describeData[srccol].get(col.expr, ''), expr=name, **kwargs)

# rowdef: Column from source sheet
class DescribeSheet(ColumnsSheet):
#    rowtype = 'columns'
    columns = [
            ColumnAttr('sheet', 'sheet'),
            ColumnAttr('column', 'name'),
            DescribeColumn('errors', type=len),
            DescribeColumn('nulls',  type=len),
            DescribeColumn('distinct',type=len),
            DescribeColumn('mode',   type=str),
            DescribeColumn('min',    type=str),
            DescribeColumn('max',    type=str),
            DescribeColumn('median', type=str),
            DescribeColumn('mean',   type=float),
            DescribeColumn('stdev',  type=float),
    ]
    colorizers = [
        RowColorizer(7, 'color_key_col', lambda s,c,r,v: r in r.sheet.keyCols),
    ]

    @asyncthread
    def reload(self):
        super().reload()
        self.rows = [c for c in self.rows if not c.hidden]
        self.describeData = { col: {} for col in self.rows }

        for srccol in Progress(self.rows):
            if not srccol.hidden:
                self.reloadColumn(srccol)
            sync(max_threads)

    @asyncthread
    def reloadColumn(self, srccol):
            d = self.describeData[srccol]
            isNull = isNullFunc()

            vals = list()
            d['errors'] = list()
            d['nulls'] = list()
            d['distinct'] = set()

            for sr in Progress(srccol.sheet.rows):
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
        r = wrapply(func, *args, **kwargs)
        d[func.__name__] = r
        return r


DescribeSheet.addCommand('zs', 'select-cell', 'cursorRow.sheet.select(cursorValue)')
DescribeSheet.addCommand('zu', 'unselect-cell', 'cursorRow.sheet.unselect(cursorValue)')
DescribeSheet.addCommand('z'+ENTER, 'dup-cell', 'isinstance(cursorValue, list) or error(cursorValue); vs=copy(cursorRow.sheet); vs.rows=cursorValue; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)')
