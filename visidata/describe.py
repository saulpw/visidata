from statistics import mode, median, mean, stdev

from visidata import *

max_threads = 2

Sheet.addCommand('I', 'describe-sheet', 'vd.push(DescribeSheet(sheet.name+"_describe", source=[sheet]))', 'open descriptive statistics for all visible columns')
globalCommand('gI', 'describe-all', 'vd.push(DescribeSheet("describe_all", source=vd.sheets))', 'open Describe Sheet with all visible columns from all sheets')

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

option('describe_aggrs', 'mean stdev', 'numeric aggregators to calculate on Describe sheet')


# rowdef: Column from source sheet
class DescribeSheet(ColumnsSheet):
#    rowtype = 'columns'
    precious = True
    columns = [
            ColumnAttr('sheet', 'sheet', width=0),
            ColumnAttr('column', 'name'),
            ColumnEnum('type', getGlobals(), width=0, default=anytype),
            DescribeColumn('errors', type=vlen),
            DescribeColumn('nulls',  type=vlen),
            DescribeColumn('distinct',type=vlen),
            DescribeColumn('mode',   type=str),
            DescribeColumn('min',    type=str),
            DescribeColumn('max',    type=str),
            DescribeColumn('sum'),
            DescribeColumn('median', type=str),
    ]
    colorizers = [
        RowColorizer(7, 'color_key_col', lambda s,c,r,v: r and r in r.sheet.keyCols),
    ]
    nKeys = 2

    @asyncthread
    def reload(self):
        super().reload()
        self.rows = [c for c in self.rows if not c.hidden]
        self.describeData = { col: {} for col in self.rows }

        self.columns = []
        for c in type(self).columns:
            self.addColumn(c)

        self.setKeys(self.columns[:self.nKeys])

        for aggrname in options.describe_aggrs.split():
            self.addColumn(DescribeColumn(aggrname, type=float))

        for srccol in Progress(self.rows, 'categorizing'):
            if not srccol.hidden:
                self.reloadColumn(srccol)

    def reloadColumn(self, srccol):
            d = self.describeData[srccol]
            isNull = isNullFunc()

            vals = list()
            d['errors'] = list()
            d['nulls'] = list()
            d['distinct'] = set()

            for sr in Progress(srccol.sheet.rows, 'calculating'):
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
                for func in [min, max, sum, median]:  # use type
                    d[func.__name__] = self.calcStatistic(d, func, vals)
                for aggrname in options.describe_aggrs.split():
                    func = globals()[aggrname]
                    d[func.__name__] = self.calcStatistic(d, func, vals)

    def calcStatistic(self, d, func, *args, **kwargs):
        r = wrapply(func, *args, **kwargs)
        d[func.__name__] = r
        return r


DescribeSheet.addCommand('zs', 'select-cell', 'cursorRow.sheet.select(cursorValue)')
DescribeSheet.addCommand('zu', 'unselect-cell', 'cursorRow.sheet.unselect(cursorValue)')
DescribeSheet.addCommand('z'+ENTER, 'dive-cell', 'isinstance(cursorValue, list) or error(cursorValue); vs=copy(cursorRow.sheet); vs.rows=cursorValue; vs.name+="_%s_%s"%(cursorRow.name,cursorCol.name); vd.push(vs)')
