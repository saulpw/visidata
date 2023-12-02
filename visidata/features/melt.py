import collections
import re
from copy import copy

from visidata import Sheet, SubColumnItem, ColumnItem, Column, Progress
from visidata import asyncthread, vd

melt_var_colname = 'Variable' # column name to use for the melted variable name
melt_value_colname = 'Value'  # column name to use for the melted value
melt_null = False   # whether to include rows for null values during melt


# rowdef: {0:sourceRow, 1:Category1, ..., N:CategoryN, ColumnName:Column, ...}
class MeltedSheet(Sheet):
    "Perform 'melt', the inverse of 'pivot', on input `source` sheet.  Pass `regex` to parse column names into additional columns"

    rowtype = 'melted values'

    def getValueCols(self) -> dict:
        '''Return dict of ('Category1', 'Category2') -> list of tuple('ColumnName', Column)'''
        colsToMelt = [copy(c) for c in self.source.nonKeyVisibleCols]

        # break down Category1_Category2_ColumnName as per regex
        valcols = collections.OrderedDict()
        for c in colsToMelt:
            c.aggregators = [vd.aggregators['max']]
            m = re.match(self.regex, c.name)
            if m:
                if len(m.groups()) == 1:
                    varvals = m.groups()
                    valcolname = melt_value_colname
                else:
                    *varvals, valcolname = m.groups()
                cats = tuple(varvals)
                if cats not in valcols:
                    valcols[cats] = []
                valcols[cats].append((valcolname, c))
                ncats = len(varvals)
            else:
                vd.status(f'"{c.name}" column does not match regex, skipping')
                ncats = 0

        return valcols

    def resetCols(self):
        self.columns = []
        sheet = self.source
        for c in sheet.keyCols:
            self.addColumn(SubColumnItem(0, c))
        self.setKeys(self.columns)

        valcols = self.getValueCols()
        othercols = set()
        ncats = 0
        for colnames, cols in valcols.items():
            ncats = max(ncats, len(colnames))
            for cname, _ in cols:
                othercols.add(cname)

        if ncats == 1:
            self.addColumn(ColumnItem(melt_var_colname, 1))
        else:
            for i in range(ncats):
                self.addColumn(ColumnItem(f'{melt_var_colname}{i+1}', i+1))

        for cname in othercols:
            self.addColumn(Column(cname,
                getter=lambda col,row,cname=cname: row[cname].getValue(row[0]),
                setter=lambda col,row,val,cname=cname: row[cname].setValues([row[0]], val),
                aggregators=[vd.aggregators['max']]))

    def iterload(self):
        isNull = self.isNullFunc()

        valcols = self.getValueCols()
        for r in Progress(self.source.rows, 'melting'):
            for colnames, cols in valcols.items():
                meltedrow = {}
                for varval, c in cols:
                    try:
                        if melt_null or not isNull(c.getValue(r)):
                            meltedrow[varval] = c
                    except Exception as e:
                        pass

                if meltedrow:  # remove rows with no content (all nulls)
                    meltedrow[0] = r
                    for i, colname in enumerate(colnames):
                        meltedrow[i+1] = colname

                    yield meltedrow


@Sheet.api
def openMelt(sheet, regex='(.*)'):
    return MeltedSheet(sheet.name, 'melted', source=sheet, regex=regex)


Sheet.addCommand('M', 'melt', 'vd.push(openMelt())', 'open Melted Sheet (unpivot), with key columns retained and all non-key columns reduced to Variable-Value rows')

Sheet.addCommand('gM', 'melt-regex', 'vd.push(openMelt(vd.inputRegex("regex to split colname: ", value="(.*)_(.*)", type="regex-capture")))', 'open Melted Sheet (unpivot), with key columns retained and regex capture groups determining how the non-key columns will be reduced to Variable-Value rows')

vd.addMenuItems('''
    Data > Melt > nonkey columns > melt
    Data > Melt > nonkey columns by regex > melt-regex
''')
