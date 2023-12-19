from copy import copy
from statistics import mode, median, mean, stdev

from visidata import vd, Column, ColumnAttr, vlen, RowColorizer, asyncthread, Progress, wrapply
from visidata import BaseSheet, TableSheet, ColumnsSheet, SheetsSheet


vd.option('describe_aggrs', 'mean stdev', 'numeric aggregators to calculate on Describe sheet', help=vd.help_aggregators)


@Column.api
def isError(col, row):
    'Return True if the computed or typed value for *row* in this column is an error.'
    try:
        v = col.getValue(row)
        if v is not None:
            col.type(v)
        return False
    except Exception as e:
        return True


class DescribeColumn(Column):
    def __init__(self, name, **kwargs):
        kwargs.setdefault('width', 10)
        super().__init__(name, getter=lambda col,srccol: col.sheet.describeData[srccol].get(col.expr, ''), expr=name, **kwargs)


# rowdef: Column from source sheet
class DescribeSheet(ColumnsSheet):
#    rowtype = 'columns'
    guide = '''
        # Describe Sheet
        This `Describe Sheet` shows a few basic metrics over data in {sheet.displaySource}, with each column represented by a row.

        For example, row {sheet.cursorRowIndex} describes the _{sheet.cursorRow.name}_ column, showing its minimum value, maximum value, mean, median, and other measures.
    '''
    precious = True
    columns = [
            ColumnAttr('sheet', 'sheet', width=0),
            ColumnAttr('column', 'name'),
            ColumnAttr('type', 'typestr', width=0),
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

    def loader(self):
        super().loader()
        self.rows = [c for c in self.rows if not c.hidden]
        self.describeData = { col: {} for col in self.rows }
        self.resetCols()

        for aggrname in vd.options.describe_aggrs.split():
            self.addColumn(DescribeColumn(aggrname, type=float))

        for srccol in Progress(self.rows, 'categorizing'):
            if not srccol.hidden:
                self.reloadColumn(srccol)

    def reloadColumn(self, srccol):
            d = self.describeData[srccol]
            isNull = srccol.sheet.isNullFunc()

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
            if vd.isNumeric(srccol):
                for func in [min, max, sum, median]:  # use type
                    d[func.__name__] = self.calcStatistic(d, func, vals)
                for aggrname in vd.options.describe_aggrs.split():
                    aggr = vd.aggregators[aggrname].funcValues
                    d[aggrname] = self.calcStatistic(d, aggr, vals)

    def calcStatistic(self, d, func, *args, **kwargs):
        r = wrapply(func, *args, **kwargs)
        d[func.__name__] = r
        return r

    def openCell(self, col, row):
        'open copy of source sheet with rows described in current cell'
        val = col.getValue(row)
        if isinstance(val, list):
            vs=copy(row.sheet)
            vs.rows=val
            vs.name+="_%s_%s"%(row.name,col.name)
            return vs
        vd.warning(val)


TableSheet.addCommand('I', 'describe-sheet', 'vd.push(DescribeSheet(sheet.name+"_describe", source=[sheet]))', 'open Describe Sheet with descriptive statistics for all visible columns')
BaseSheet.addCommand('gI', 'describe-all', 'vd.push(DescribeSheet("describe_all", source=vd.stackedSheets))', 'open Describe Sheet with description statistics for all visible columns from all sheets')
SheetsSheet.addCommand('gI', 'describe-selected', 'vd.push(DescribeSheet("describe_all", source=selectedRows))', 'open Describe Sheet with all visible columns from selected sheets')

DescribeSheet.addCommand('zs', 'select-cell', 'cursorRow.sheet.select(cursorValue)', 'select rows on source sheet which are being described in current cell')
DescribeSheet.addCommand('zu', 'unselect-cell', 'cursorRow.sheet.unselect(cursorValue)', 'unselect rows on source sheet which are being described in current cell')

vd.addMenuItems('Data > Statistics > describe-sheet')

vd.addGlobals({'DescribeSheet':DescribeSheet})
