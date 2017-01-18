from visidata import *

command('S', 'vd.push(SheetsSheet())', 'open Sheet stack')
command('C', 'vd.push(SheetColumns(sheet))', 'open Columns for this sheet')

option('ColumnStats', False, 'include mean/median/etc on Column sheet')
command(':', 'splitColumn(sheet, cursorCol, cursorValue, input("split char: ") or None)', 'split column by the given char')


def splitColumn(sheet, origcol, exampleVal, ch):
    maxcols = len(exampleVal.split(ch))
    if maxcols <= 1:
        return status('move cursor to valid example row to split by this column')

    for i in range(maxcols):
        sheet.columns.insert(sheet.cursorColIndex+i+1, (Column("%s[%s]" % (origcol.name, i), getter=lambda r,c=origcol,ch=ch,i=i: c.getValue(r).split(ch)[i])))
    origcol.width = 0


class SheetsSheet(SheetList):
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
    def __init__(self, srcsheet):
        super().__init__(srcsheet.name + '_columns', srcsheet)

        # on the Columns sheet, these affect the 'row' (column in the source sheet)
        self.command('@', 'cursorRow.type = date; cursorDown(+1)', 'set source column type to datetime')
        self.command('#', 'cursorRow.type = int; cursorDown(+1)', 'set source column type to integer')
        self.command('$', 'cursorRow.type = str; cursorDown(+1)', 'set source column type to string')
        self.command('%', 'cursorRow.type = float; cursorDown(+1)', 'set source column type to decimal numeric type')
        self.command('~', 'cursorRow.type = detectType(cursorRow.getValue(source.cursorRow)); cursorDown(+1)', 'autodetect type of source column using its data')
        self.command('!', 'source.toggleKeyColumn(cursorRowIndex)', 'toggle key column on source sheet')
        self.command('-', 'cursorRow.width = 0', 'hide column on source sheet')
        self.command('_', 'cursorRow.width = cursorRow.getMaxWidth(source.visibleRows)', 'set source column width to max width of its rows')

        self.command('+', 'rows.insert(cursorRowIndex+1, Column("+".join(c.name for c in selectedRows), getter=lambda r,cols=selectedRows,ch=input("join char: "): ch.join(filter(None, (c.getValue(r) for c in cols)))))', 'join columns with the given char')
        self.command('g-', 'for c in selectedRows: c.width = 0', 'hide all selected columns on source sheet')
        self.command('g_', 'for c in selectedRows: c.width = c.getMaxWidth(source.visibleRows)', 'set widths of all selected columns to the max needed for the screen')


    def reload(self):
        self.rows = self.source.columns
        self.cursorRowIndex = self.source.cursorColIndex
        self.columns = [
            ColumnAttr('name', str),
            ColumnAttr('width', int),
            Column('type',   str, lambda r: r.type.__name__),
            ColumnAttr('fmtstr', str),
            ColumnAttr('expr', str),
            Column('value',  anytype, lambda c,sheet=self.source: c.getValue(sheet.cursorRow)),
        ]

        if options.ColumnStats:
            self.columns.extend([
                Column('nulls',  int, lambda c,sheet=sheet: c.nEmpty(sheet.rows)),
                Column('uniques',  int, lambda c,sheet=sheet: len(set(c.values(sheet.rows))), width=0),
                Column('mode',   anytype, lambda c: statistics.mode(c.values(sheet.rows)), width=0),
                Column('min',    anytype, lambda c: min(c.values(sheet.rows)), width=0),
                Column('median', anytype, lambda c: statistics.median(c.values(sheet.rows)), width=0),
                Column('mean',   float, lambda c: statistics.mean(c.values(sheet.rows)), width=0),
                Column('max',    anytype, lambda c: max(c.values(sheet.rows)), width=0),
                Column('stddev', float, lambda c: statistics.stdev(c.values(sheet.rows)), width=0),
            ])


#### slicing and dicing
class SheetJoin(Sheet):
    def __init__(self, sheets, jointype='&'):
        super().__init__(jointype.join(vs.name for vs in sheets), sheets)
        self.jointype = jointype

    def reload(self):
        sheets = self.source

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = [SubrowColumn(ColumnItem(c.name, i), 0) for i, c in enumerate(sheets[0].columns[:sheets[0].nKeys])]
        self.nKeys = sheets[0].nKeys

        rowsBySheetKey = {}
        rowsByKey = {}

        for vs in sheets:
            rowsBySheetKey[vs] = {}
            for r in vs.rows:
                key = tuple(c.getValue(r) for c in vs.keyCols)
                rowsBySheetKey[vs][key] = r

        for sheetnum, vs in enumerate(sheets):
            # subsequent elements are the rows from each source, in order of the source sheets
            self.columns.extend(SubrowColumn(c, sheetnum+1) for c in vs.columns[vs.nKeys:])
            for r in vs.rows:
                key = tuple(str(c.getValue(r)) for c in vs.keyCols)
                if key not in rowsByKey:
                    rowsByKey[key] = [key] + [rowsBySheetKey[vs2].get(key) for vs2 in sheets]  # combinedRow

        if self.jointype == '&':  # inner join  (only rows with matching key on all sheets)
            self.rows = list(combinedRow for k, combinedRow in rowsByKey.items() if all(combinedRow))
        elif self.jointype == '+':  # outer join (all rows from first sheet)
            self.rows = list(combinedRow for k, combinedRow in rowsByKey.items() if combinedRow[1])
        elif self.jointype == '*':  # full join (keep all rows from all sheets)
            self.rows = list(combinedRow for k, combinedRow in rowsByKey.items())
        elif self.jointype == '~':  # diff join (only rows without matching key on all sheets)
            self.rows = list(combinedRow for k, combinedRow in rowsByKey.items() if not all(combinedRow))
