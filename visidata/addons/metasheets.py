from visidata import *

globalCommand('X', 'vd.push(SheetDict("lastInputs", vd.lastInputs))', 'push last inputs sheet')

option('col_stats', False, 'include mean/median/etc on Column sheet')

class OptionsSheet(Sheet):
    'options viewing and editing'
    commands = [Command(ENTER, 'source[cursorRow[0]] = editCell(1)', 'edit this option')]
    def __init__(self, d):
        super().__init__('options', d)
        self.columns = ArrayNamedColumns('option value default description'.split())
        self.addColorizer('cell', 9, lambda s,c,r,v: v if c.name in ['value', 'default'] and r[0].startswith('color_') else None)
        self.nKeys = 1

    def reload(self):
        self.rows = list(self.source._opts.values())

vd().optionsSheet = OptionsSheet(options)

def combineColumns(cols):
    'Return Column object formed by joining fields in given columns.'
    return Column("+".join(c.name for c in cols),
                  getter=lambda r,cols=cols,ch=options.field_joiner: ch.join(filter(None, (c.getValue(r) for c in cols))))


class SheetsSheet(Sheet):
    commands = [
        Command(ENTER, 'moveListItem(vd.sheets, cursorRowIndex, 0); vd.sheets.pop(1)', 'jump to this sheet'),
        Command('&', 'vd.replace(SheetJoin(selectedRows, jointype="&"))', 'open inner join of selected sheets'),
        Command('+', 'vd.replace(SheetJoin(selectedRows, jointype="+"))', 'open outer join of selected sheets'),
        Command('*', 'vd.replace(SheetJoin(selectedRows, jointype="*"))', 'open full join of selected sheets'),
        Command('~', 'vd.replace(SheetJoin(selectedRows, jointype="~"))', 'open diff join of selected sheets'),
    ]
    columns = AttrColumns('name progressPct nRows nCols nVisibleCols cursorValue keyColNames source'.split())
    def reload(self):
        self.rows = vd().sheets


class ColumnsSheet(Sheet):
    commands = [
        # on the Columns sheet, these affect the 'row' (column in the source sheet)
        Command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows))', 'join selected source columns'),
        Command('g!', 'for c in selectedRows: source.toggleKeyColumn(source.columns.index(c))', 'toggle all selected column as keys on source sheet'),
        Command('g+', 'columns[4].setValues(sheet, selectedRows, chooseOne(aggregators.keys()))', 'choose aggregator for this column'),
        Command('g-', 'for c in selectedRows: c.width = 0', 'hide all selected columns on source sheet'),
        Command('g_', 'for c in selectedRows: c.width = c.getMaxWidth(source.visibleRows)', 'set widths of all selected columns to the max needed for the screen'),
        Command('g%', 'for c in selectedRows: c.type = float', 'set type of all selected columns to float'),
        Command('g#', 'for c in selectedRows: c.type = int', 'set type of all selected columns to int'),
        Command('g@', 'for c in selectedRows: c.type = date', 'set type of all selected columns to date'),
        Command('g$', 'for c in selectedRows: c.type = currency', 'set type of all selected columns to currency'),
        Command('g~', 'for c in selectedRows: c.type = str', 'set type of all selected columns to string'),
    ]

    def __init__(self, srcsheet):
        super().__init__(srcsheet.name + '_columns', srcsheet)

        self.addColorizer('row', 8, lambda self,c,r,v: options.color_key_col if r in self.source.keyCols else None)

        self.columns = [
            ColumnAttr('name', type=str),
            ColumnAttr('width', type=int),
            ColumnAttrNamedObject('type'),
            ColumnAttr('fmtstr', type=str),
            ColumnAttrNamedObject('aggregator'),
            ColumnAttr('expr', type=str),
            Column('value',  type=anytype, getter=lambda c,sheet=self.source: c.getDisplayValue(sheet.cursorRow)),
        ]

    def reload(self):
        self.rows = self.source.columns
        self.cursorRowIndex = self.source.cursorColIndex

        if options.col_stats:
            import statistics

            self.columns.extend([
                Column('nulls',  type=int, getter=lambda c,sheet=self.source: c.nEmpty(sheet.rows)),
                Column('uniques',  type=int, getter=lambda c,sheet=self.source: len(set(c.values(sheet.rows)))),
                Column('mode',   type=anytype, getter=lambda c,sheet=self.source: statistics.mode(c.values(sheet.rows))),
                Column('min',    type=anytype, getter=lambda c,sheet=self.source: min(c.values(sheet.rows))),
                Column('median', type=anytype, getter=lambda c,sheet=self.source: statistics.median(c.values(sheet.rows))),
                Column('mean',   type=float, getter=lambda c,sheet=self.source: statistics.mean(c.values(sheet.rows))),
                Column('max',    type=anytype, getter=lambda c,sheet=self.source: max(c.values(sheet.rows))),
                Column('stddev', type=float, getter=lambda c,sheet=self.source: statistics.stdev(c.values(sheet.rows))),
            ])


#### slicing and dicing
class SheetJoin(Sheet):
    '''Implement four kinds of JOIN.

     * `&`: inner JOIN (default)
     * `*`: full outer JOIN
     * `+`: left outer JOIN
     * `~`: "diff" or outer excluding JOIN, i.e., full JOIN minus inner JOIN'''

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
                self.addRow(combinedRow)

            elif self.jointype == '&':  # inner join  (only rows with matching key on all sheets)
                if all(combinedRow):
                    self.addRow(combinedRow)

            elif self.jointype == '+':  # outer join (all rows from first sheet)
                if combinedRow[1]:
                    self.addRow(combinedRow)

            elif self.jointype == '~':  # diff join (only rows without matching key on all sheets)
                if not all(combinedRow):
                    self.addRow(combinedRow)
