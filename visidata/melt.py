import collections
import re

from visidata import *


melt_var_colname = 'Variable' # column name to use for the melted variable name
melt_value_colname = 'Value'  # column name to use for the melted value
melt_null = False   # whether to melt null values


# rowdef: {0:sourceRow, 1:Category1, ..., N:CategoryN, ColumnName:Column, ...}
class MeltedSheet(Sheet):
    "Perform 'melt', the inverse of 'pivot', on input sheet."

    rowtype = 'melted values'

    @asyncthread
    def reload(self):
        self.columns = []
        isNull = self.isNullFunc()

        sheet = self.source
        for c in sheet.keyCols:
            self.addColumn(SubColumnItem(0, c))
        self.setKeys(self.columns)

        colsToMelt = [copy(c) for c in sheet.nonKeyVisibleCols]

        # break down Category1_Category2_ColumnName as per regex
        valcols = collections.OrderedDict()  # ('Category1', 'Category2') -> list of tuple('ColumnName', Column)
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
                vd.status('"%s" column does not match regex, skipping' % c.name)
                ncats = 0

        othercols = set()
        for colnames, cols in valcols.items():
            for cname, _ in cols:
                othercols.add(cname)

        if ncats == 1:
            self.addColumn(ColumnItem(melt_var_colname, 1))
        else:
            for i in range(ncats):
                self.addColumn(ColumnItem('%s%d' % (melt_var_colname, i+1), i+1))

        for cname in othercols:
            self.addColumn(Column(cname,
                getter=lambda col,row,cname=cname: row[cname].getValue(row[0]),
                setter=lambda col,row,val,cname=cname: row[cname].setValues([row[0]], val),
                aggregators=[vd.aggregators['max']]))

        self.rows = []
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

                    self.addRow(meltedrow)


@Sheet.api
def openMelt(sheet, regex='(.*)'):
    return MeltedSheet(sheet.name, 'melted', source=sheet, regex=regex)


Sheet.addCommand('M', 'melt', 'vd.push(openMelt())', 'open Melted Sheet (unpivot), with key columns retained and all non-key columns reduced to Variable-Value rows')


Sheet.addCommand('gM', 'melt-regex', 'vd.push(openMelt(vd.input("regex to split colname: ", value="(.*)_(.*)", type="regex-capture")))', 'open Melted Sheet (unpivot), with key columns retained and regex capture groups determining how the non-key columns will be reduced to Variable-Value rows')
