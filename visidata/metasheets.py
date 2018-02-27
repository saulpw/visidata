from visidata import *

OptionsSheet.colorizers += [
        Colorizer('cell', 9, lambda s,c,r,v: v if c.name in ['value', 'default'] and r[0].startswith('color_') else None)
    ]

def combineColumns(cols):
    'Return Column object formed by joining fields in given columns.'
    return Column("+".join(c.name for c in cols),
                  getter=lambda col,row,cols=cols,ch=' ': ch.join(c.getDisplayValue(row) for c in cols))

def createJoinedSheet(sheets, jointype=''):
    if jointype == 'append':
        return SheetConcat('&'.join(vs.name for vs in sheets), sources=sheets)
    else:
        return SheetJoin('+'.join(vs.name for vs in sheets), sources=sheets, jointype=jointype)

jointypes = {k:k for k in ["inner", "outer", "full", "diff", "append"]}

SheetsSheet.commands += [
        Command('&', 'vd.replace(createJoinedSheet(selectedRows, jointype=chooseOne(jointypes)))', 'merge the selected sheets with visible columns from all, keeping rows according to jointype', 'sheet-join'),
        Command('gC', 'vd.push(ColumnsSheet("all_columns", source=selectedRows or rows[1:]))', 'open Columns Sheet with all columns from selected sheets', 'sheet-columns-selected'),
    ]

SheetsSheet.columns.append(ColumnAttr('progressPct'))

# used ColumnsSheet, affecting the 'row' (source column)
columnCommands = [
        Command('g!', 'for c in selectedRows or [cursorRow]: source.toggleKeyColumn(c)', 'toggle selected rows as key columns on source sheet'),
        Command('gz!', 'for c in selectedRows or [cursorRow]: source.keyCols.remove(c)', 'unset selected rows as key columns on source sheet'),
        Command('g-', 'for c in selectedRows or source.nonKeyVisibleCols: c.width = 0', 'hide selected source columns on source sheet'),
        Command('g%', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = float', 'set type of selected source columns to float'),
        Command('g#', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = int', 'set type of selected source columns to int'),
        Command('g@', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = date', 'set type of selected source columns to date'),
        Command('g$', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = currency', 'set type of selected columns to currency'),
        Command('g~', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = str', 'set type of selected columns to str'),
        Command('gz~', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = anytype', 'set type of selected columns to anytype'),
    ]

ColumnsSheet.commands += columnCommands + [
        Command('column-source-width-max', 'for c in selectedRows or source.nonKeyVisibleCols: c.width = c.getMaxWidth(source.visibleRows)', 'adjust widths of selected source columns'),
        Command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows))', 'add column from concatenating selected source columns'),
]
DescribeSheet.commands += columnCommands


ColumnsSheet.columns += [
        ColumnAttr('expr'),
    ]

#### slicing and dicing
# rowdef: [(key, ...), sheet1_row, sheet2_row, ...]
#   if a sheet does not have this key, sheet#_row is None
class SheetJoin(Sheet):
    'Column-wise join/merge. `jointype` constructor arg should be one of jointypes.'

    @async
    def reload(self):
        sheets = self.sources

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = []
        for i, c in enumerate(sheets[0].keyCols):
            self.addColumn(SubrowColumn(ColumnItem(c.name, i), 0))
        self.keyCols = self.columns[:]

        rowsBySheetKey = {}
        rowsByKey = {}

        with Progress(total=sum(len(vs.rows) for vs in sheets)*2) as prog:
            for vs in sheets:
                # tally rows by keys for each sheet
                rowsBySheetKey[vs] = collections.defaultdict(list)
                for r in vs.rows:
                    prog.addProgress(1)
                    key = tuple(c.getTypedValueNoExceptions(r) for c in vs.keyCols)
                    rowsBySheetKey[vs][key].append(r)

            for sheetnum, vs in enumerate(sheets):
                # subsequent elements are the rows from each source, in order of the source sheets
                for c in vs.nonKeyVisibleCols:
                    self.addColumn(SubrowColumn(c, sheetnum+1))
                for r in vs.rows:
                    prog.addProgress(1)
                    key = tuple(c.getTypedValueNoExceptions(r) for c in vs.keyCols)
                    if key not in rowsByKey: # gather for this key has not been done yet
                        # multiplicative for non-unique keys
                        rowsByKey[key] = []
                        for crow in itertools.product(*[rowsBySheetKey[vs2].get(key, [None]) for vs2 in sheets]):
                            rowsByKey[key].append([key] + list(crow))

        self.rows = []

        with Progress(total=len(rowsByKey)) as prog:
            for k, combinedRows in rowsByKey.items():
                prog.addProgress(1)

                if self.jointype == 'full':  # keep all rows from all sheets
                    for combinedRow in combinedRows:
                        self.addRow(combinedRow)

                elif self.jointype == 'inner':  # only rows with matching key on all sheets
                    for combinedRow in combinedRows:
                        if all(combinedRow):
                            self.addRow(combinedRow)

                elif self.jointype == 'outer':  # all rows from first sheet
                    for combinedRow in combinedRows:
                        if combinedRow[1]:
                            self.addRow(combinedRow)

                elif self.jointype == 'diff':  # only rows without matching key on all sheets
                    for combinedRow in combinedRows:
                        if not all(combinedRow):
                            self.addRow(combinedRow)

class ColumnConcat(Column):
    def __init__(self, name, colsBySheet, **kwargs):
        super().__init__(name, **kwargs)
        self.colsBySheet = colsBySheet

    def calcValue(self, row):
        srcSheet, srcRow = row
        srcCol = self.colsBySheet.get(srcSheet, None)
        if srcCol:
            return srcCol.calcValue(srcRow)

    def setValue(self, row, v):
        srcSheet, srcRow = row
        srcCol = self.colsBySheet.get(srcSheet, None)
        if srcCol:
            srcCol.setValue(srcRow, v)
        else:
            error('column not on source sheet')

# rowdef: (Sheet, row)
class SheetConcat(Sheet):
    'combination of multiple sheets by row concatenation'
    def reload(self):
        self.rows = []
        for sheet in self.sources:
            for r in sheet.rows:
                self.addRow((sheet, r))

        self.columns = []
        allColumns = {}
        for srcsheet in self.sources:
            for srccol in srcsheet.visibleCols:
                colsBySheet = allColumns.get(srccol.name, None)
                if colsBySheet is None:
                    colsBySheet = {}  # dict of [Sheet] -> Column
                    allColumns[srccol.name] = colsBySheet
                    if isinstance(srccol, ColumnExpr):
                        combinedCol = copy(srccol)
                    else:
                        combinedCol = ColumnConcat(srccol.name, colsBySheet, type=srccol.type)
                    self.addColumn(combinedCol)

                if srcsheet in colsBySheet:
                    status('%s has multiple columns named "%s"' % (srcsheet.name, srccol.name))

                colsBySheet[srcsheet] = srccol

        self.recalc()  # to set .sheet on columns, needed if this reload becomes async
