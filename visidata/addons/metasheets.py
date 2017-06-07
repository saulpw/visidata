from visidata import *

command('S', 'vd.push(SheetsSheet())', 'open Sheet stack')
command('C', 'vd.push(SheetColumns(sheet))', 'open Columns for this sheet')

option('col_stats', False, 'include mean/median/etc on Column sheet')
command(':', 'splitColumn(columns, cursorColIndex, cursorCol, cursorValue, input("split char: ") or None)', 'split column by the given char')
command('=', 'addColumn(ColumnExpr(sheet, input("new column expr=", "expr")), index=cursorColIndex+1)', 'add column by expr')

def _getattrname(o, k):
    v = getattr(o, k)
    return v.__name__ if v else None

def ColumnGlobal(name):
    """Return Column object with given name."""
    return Column(name, getter=lambda r,name=name: _getattrname(r, name),
                        setter=lambda r,v,name=name: setattr(r, name, v))

option('split_max', -1, 'string.split limit')
# exampleVal just to know how many subcolumns to make
def splitColumn(columns, colIndex, origcol, exampleVal, ch):
    """Split selected column, up to maximum in options,  on character `ch`."""
    split_max = int(options.split_max)

    if ch:
        maxcols = len(exampleVal.split(ch, split_max))
    else:
        maxcols = len(exampleVal)

    if maxcols <= 1:
        return status('move cursor to valid example row to split by this column')

    for i in range(maxcols):
        if ch:
            columns.insert(colIndex+i+1, (Column("%s_%s" % (origcol.name, i), getter=lambda r,c=origcol,ch=ch,i=i,split_max=split_max: c.getValue(r).split(ch, split_max)[i])))
        else:
            columns.insert(colIndex+i+1, (Column("%s_%s" % (origcol.name, i), getter=lambda r,c=origcol,ch=ch,i=i,split_max=split_max: c.getValue(r)[i])))


class LazyMapping:
    """Calculate column values as needed."""
    def __init__(self, sheet, row):
        self.row = row
        self.sheet = sheet

    def keys(self):
        return [c.name for c in self.sheet.columns]

    def __call__(self, col):
        return eval(col.expr, {}, self)

    def __getitem__(self, colname):
        colnames = [c.name for c in self.sheet.columns]
        if colname in colnames:
            colidx = colnames.index(colname)
            return self.sheet.columns[colidx].getValue(self.row)
        else:
            raise KeyError(colname)

    def __getattr__(self, colname):
        return self.__getitem__(colname)


def ColumnExpr(sheet, expr):
    """Create new `Column` from Python expression."""
    if expr:
        vc = Column(expr)  # or default name?
        vc.expr = expr
        vc.getter = lambda r,c=vc,s=sheet: LazyMapping(s, r)(c)
        return vc


class SheetsSheet(SheetList):
    """Open Sheet stack."""
    def __init__(self):
        super().__init__('sheets', vd().sheets, columns=AttrColumns('name progressPct nRows nCols nVisibleCols cursorValue keyColNames source'.split()))

    def reload(self):
        super().reload()
        self.rows = vd().sheets
        self.command('^J', 'moveListItem(vd.sheets, cursorRowIndex, 0); vd.sheets.pop(1)', 'jump to this sheet')
        self.command('&', 'vd.replace(SheetJoin(selectedRows, jointype="&"))', 'open inner join of selected sheets')
        self.command('+', 'vd.replace(SheetJoin(selectedRows, jointype="+"))', 'open outer join of selected sheets')
        self.command('*', 'vd.replace(SheetJoin(selectedRows, jointype="*"))', 'open full join of selected sheets')
        self.command('~', 'vd.replace(SheetJoin(selectedRows, jointype="~"))', 'open diff join of selected sheets')


class SheetColumns(Sheet):
    """Open Columns for Sheet."""
    def __init__(self, srcsheet):
        super().__init__(srcsheet.name + '_columns', srcsheet)

        # on the Columns sheet, these affect the 'row' (column in the source sheet)
        self.command('@', 'cursorRow.type = date; cursorDown(+1)', 'set source column type to datetime')
        self.command('#', 'cursorRow.type = int; cursorDown(+1)', 'set source column type to integer')
        self.command('$', 'cursorRow.type = str; cursorDown(+1)', 'set source column type to string')
        self.command('%', 'cursorRow.type = float; cursorDown(+1)', 'set source column type to decimal numeric type')
        self.command('~', 'cursorRow.type = detectType(cursorRow.getValue(source.cursorRow)); cursorDown(+1)', 'autodetect type of source column using its data')
        self.command('!', 'source.toggleKeyColumn(cursorRowIndex); cursorDown(+1)', 'toggle key column on source sheet')
        self.command('-', 'cursorRow.width = 0; cursorDown(+1)', 'hide column on source sheet')
        self.command('_', 'cursorRow.width = cursorRow.getMaxWidth(source.visibleRows); cursorDown(+1)', 'set source column width to max width of its rows')
        self.command(':', 'splitColumn(source.columns, cursorRowIndex, cursorRow, cursorRow.getValue(sheet.cursorRow), input("split char: ") or None)', 'create new columns by splitting current column')
        self.command('=', 'source.addColumn(ColumnExpr(source, input("new column expr=", "expr")), index=cursorRowIndex+1)', 'add column by expr')

        self.command('+', 'cursorRow.aggregator = chooseOne(aggregators)', 'choose aggregator for this column')
        self.command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows))', 'join selected source columns')
        self.command('g-', 'for c in selectedRows: c.width = 0', 'hide all selected columns on source sheet')
        self.command('g_', 'for c in selectedRows: c.width = c.getMaxWidth(source.visibleRows)', 'set widths of all selected columns to the max needed for the screen')
        self.command('g%', 'for c in selectedRows: c.type = float', 'set type of all selected columns to float')
        self.command('g#', 'for c in selectedRows: c.type = int', 'set type of all selected columns to int')
        self.command('g@', 'for c in selectedRows: c.type = date', 'set type of all selected columns to date')
        self.command('g$', 'for c in selectedRows: c.type = str', 'set type of all selected columns to string')

        self.command('W', 'vd.replace(SheetPivot(source, selectedRows))', 'push a pivot table, keeping nonselected keys, making variables from selected columns, and creating a column for each variable-aggregate combination')

        self.colorizers.append(lambda self,c,r,v: (options.color_key_col, 8) if r in self.source.keyCols else None)

    def reload(self):
        self.rows = self.source.columns
        self.cursorRowIndex = self.source.cursorColIndex
        self.columns = [
            ColumnAttr('name', str),
            ColumnAttr('width', int),
            ColumnGlobal('type'),
            ColumnAttr('fmtstr', str),
            ColumnGlobal('aggregator'),
            ColumnAttr('expr', str),
            Column('value',  anytype, lambda c,sheet=self.source: c.getValue(sheet.cursorRow)),
        ]

        if options.col_stats:
            self.columns.extend([
                Column('nulls',  int, lambda c,sheet=self: c.nEmpty(sheet.rows)),
                Column('uniques',  int, lambda c,sheet=self: len(set(c.values(sheet.rows))), width=0),
                Column('mode',   anytype, lambda c,sheet=self: statistics.mode(c.values(sheet.rows)), width=0),
                Column('min',    anytype, lambda c,sheet=self: min(c.values(sheet.rows)), width=0),
                Column('median', anytype, lambda c,sheet=self: statistics.median(c.values(sheet.rows)), width=0),
                Column('mean',   float, lambda c,sheet=self: statistics.mean(c.values(sheet.rows)), width=0),
                Column('max',    anytype, lambda c,sheet=self: max(c.values(sheet.rows)), width=0),
                Column('stddev', float, lambda c,sheet=self: statistics.stdev(c.values(sheet.rows)), width=0),
            ])


#### slicing and dicing
class SheetJoin(Sheet):
    """Implement four kinds of JOIN.

     * `&`: inner JOIN (default)
     * `*`: full outer JOIN
     * `+`: left outer JOIN
     * "~": "diff" or outer excluding JOIN, i.e., full JOIN minus inner JOIN"""

    def __init__(self, sheets, jointype='&'):
        super().__init__(jointype.join(vs.name for vs in sheets), sheets)
        self.jointype = jointype

    @async
    def reload(self):
        sheets = self.source

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = [SubrowColumn(ColumnItem(c.name, i), 0) for i, c in enumerate(sheets[0].columns[:sheets[0].nKeys])]
        self.nKeys = sheets[0].nKeys

        rowsBySheetKey = {}
        rowsByKey = {}

        self.progressMade = 0
        self.progressTotal = sum(len(vs.rows) for vs in sheets)*2

        for vs in sheets:
            rowsBySheetKey[vs] = {}
            for r in vs.rows:
                self.progressMade += 1
                key = tuple(c.getValue(r) for c in vs.keyCols)
                rowsBySheetKey[vs][key] = r

        for sheetnum, vs in enumerate(sheets):
            # subsequent elements are the rows from each source, in order of the source sheets
            self.columns.extend(SubrowColumn(c, sheetnum+1) for c in vs.columns[vs.nKeys:])
            for r in vs.rows:
                self.progressMade += 1
                key = tuple(str(c.getValue(r)) for c in vs.keyCols)
                if key not in rowsByKey:
                    rowsByKey[key] = [key] + [rowsBySheetKey[vs2].get(key) for vs2 in sheets]  # combinedRow

        self.rows = []
        self.progressMade = 0
        self.progressTotal = len(rowsByKey)

        for k, combinedRow in rowsByKey.items():
            self.progressMade += 1

            if self.jointype == '*':  # full join (keep all rows from all sheets)
                self.rows.append(combinedRow)

            elif self.jointype == '&':  # inner join  (only rows with matching key on all sheets)
                if all(combinedRow):
                    self.rows.append(combinedRow)

            elif self.jointype == '+':  # outer join (all rows from first sheet)
                if combinedRow[1]:
                    self.rows.append(combinedRow)

            elif self.jointype == '~':  # diff join (only rows without matching key on all sheets)
                if not all(combinedRow):
                    self.rows.append(combinedRow)
