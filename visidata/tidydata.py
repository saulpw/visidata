from visidata import *

Sheet.addCommand('M', 'melt', 'vd.push(MeltedSheet(sheet))')
Sheet.addCommand('gM', 'melt-regex', 'vd.push(MeltedSheet(sheet, regex=input("regex to split colname: ", value="(.*)_(.*)", type="regex-capture")))')

melt_var_colname = 'Variable' # column name to use for the melted variable name
melt_value_colname = 'Value'  # column name to use for the melted value


# rowdef: {0:sourceRow, 1:Category1, ..., N:CategoryN, ColumnName:Column, ...}
class MeltedSheet(Sheet):
    "Perform 'melt', the inverse of 'pivot', on input sheet."

    rowtype = 'melted values'

    def __init__(self, sheet, regex='(.*)', **kwargs):
        super().__init__(sheet.name + '_melted', source=sheet, **kwargs)
        self.regex = regex

    @asyncthread
    def reload(self):
        isNull = isNullFunc()

        sheet = self.source
        self.columns = [SubrowColumn(c.name, c, 0) for c in sheet.keyCols]
        self.setKeys(self.columns)

        colsToMelt = [copy(c) for c in sheet.nonKeyVisibleCols]

        # break down Category1_Category2_ColumnName as per regex
        valcols = collections.OrderedDict()  # ('Category1', 'Category2') -> list of tuple('ColumnName', Column)
        for c in colsToMelt:
            c.aggregators = [aggregators['max']]
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
                status('"%s" column does not match regex, skipping' % c.name)

        othercols = set()
        for colnames, cols in valcols.items():
            for cname, _ in cols:
                othercols.add(cname)

        if ncats == 1:
            self.columns.append(ColumnItem(melt_var_colname, 1))
        else:
            for i in range(ncats):
                self.columns.append(ColumnItem('%s%d' % (melt_var_colname, i+1), i+1))

        for cname in othercols:
            self.columns.append(Column(cname,
                getter=lambda col,row,cname=cname: row[cname].getValue(row[0]),
                setter=lambda col,row,val,cname=cname: row[cname].setValue(row[0], val),
                aggregators=[aggregators['max']]))

        self.rows = []
        for r in Progress(self.source.rows):
            for colnames, cols in valcols.items():
                meltedrow = {}
                for varval, c in cols:
                    try:
                        if not isNull(c.getValue(r)):
                            meltedrow[varval] = c
                    except Exception as e:
                        pass

                if meltedrow:  # remove rows with no content (all nulls)
                    meltedrow[0] = r
                    for i, colname in enumerate(colnames):
                        meltedrow[i+1] = colname

                    self.addRow(meltedrow)
