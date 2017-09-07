from visidata import *

globalCommand('X', 'vd.push(SheetDict("lastInputs", vd.lastInputs))', 'push last inputs sheet')

OptionsSheet.colorizers += [
        Colorizer('cell', 9, lambda s,c,r,v: v if c.name in ['value', 'default'] and r[0].startswith('color_') else None)
    ]

def combineColumns(cols):
    'Return Column object formed by joining fields in given columns.'
    return Column("+".join(c.name for c in cols),
                  getter=lambda r,cols=cols,ch=' ': ch.join(c.getDisplayValue(r) for c in cols))


SheetsSheet.commands += [
        Command('&', 'vd.replace(SheetJoin(selectedRows, jointype="&"))', 'open inner join of selected sheets'),
        Command('+', 'vd.replace(SheetJoin(selectedRows, jointype="+"))', 'open outer join of selected sheets'),
        Command('*', 'vd.replace(SheetJoin(selectedRows, jointype="*"))', 'open full join of selected sheets'),
        Command('~', 'vd.replace(SheetJoin(selectedRows, jointype="~"))', 'open diff join of selected sheets'),
    ]

SheetsSheet.columns.insert(1, ColumnAttr('progressPct'))


ColumnsSheet.commands += [
        # on the Columns sheet, these affect the 'row' (column in the source sheet)
        Command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows))', 'join selected source columns'),
        Command('g!', 'for c in selectedRows: source.toggleKeyColumn(source.columns.index(c))', 'toggle all selected column as keys on source sheet'),
        Command('g+', 'columns[4].setValues(selectedRows, chooseOne(aggregators.keys()))', 'choose aggregator for this column'),
        Command('g-', 'for c in selectedRows: c.width = 0', 'hide all selected columns on source sheet'),
        Command('g_', 'for c in selectedRows: c.width = c.getMaxWidth(source.visibleRows)', 'set widths of all selected columns to the max needed for the screen'),
        Command('g%', 'for c in selectedRows: c.type = float', 'set type of all selected columns to float'),
        Command('g#', 'for c in selectedRows: c.type = int', 'set type of all selected columns to int'),
        Command('g@', 'for c in selectedRows: c.type = date', 'set type of all selected columns to date'),
        Command('g$', 'for c in selectedRows: c.type = currency', 'set type of all selected columns to currency'),
        Command('g~', 'for c in selectedRows: c.type = str', 'set type of all selected columns to string'),
    ]


ColumnsSheet.columns += [
        ColumnEnum('aggregator', aggregators),
        ColumnAttr('expr'),
    ]

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
                key = tuple(c.getTypedValue(r) for c in vs.keyCols)
                rowsBySheetKey[vs][key] = r

        for sheetnum, vs in enumerate(sheets):
            # subsequent elements are the rows from each source, in order of the source sheets
            self.columns.extend(SubrowColumn(c, sheetnum+1) for c in vs.columns[vs.nKeys:])
            for r in vs.rows:
                self.progressMade += 1
                key = tuple(c.getTypedValue(r) for c in vs.keyCols)
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
