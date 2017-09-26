from visidata import *

OptionsSheet.colorizers += [
        Colorizer('cell', 9, lambda s,c,r,v: v if c.name in ['value', 'default'] and r[0].startswith('color_') else None)
    ]

def combineColumns(cols):
    'Return Column object formed by joining fields in given columns.'
    return Column("+".join(c.name for c in cols),
                  getter=lambda r,cols=cols,ch=' ': ch.join(c.getDisplayValue(r) for c in cols))

def createJoinedSheet(sheets, jointype=''):
    if jointype == 'append':
        return SheetConcat('&'.join(vs.name for vs in sheets), *sheets)
    else:
        return SheetJoin('+'.join(vs.name for vs in sheets), *sheets, jointype=jointype)

jointypes = ["inner", "outer", "full", "diff", "append"]

SheetsSheet.commands += [
        Command('&', 'vd.replace(createJoinedSheet(selectedRows, jointype=chooseOne(jointypes)))', 'merges the selected sheets with visible columns from all, keeping rows accoring to jointype'),
    ]

SheetsSheet.columns.insert(1, ColumnAttr('progressPct'))


ColumnsSheet.commands += [
        # on the Columns sheet, these affect the 'row' (column in the source sheet)
        Command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows))', 'adds column from concatenating selected source columns'),
        Command('g!', 'for c in selectedRows or [cursorRow]: source.toggleKeyColumn(source.columns.index(c))', 'toggles selected columns as keys on source sheet'),
        Command('g-', 'for c in selectedRows or source.nonKeyVisibleCols: c.width = 0', 'hides selected columns on source sheet'),
        Command('g_', 'for c in selectedRows or [cursorRow]: c.width = c.getMaxWidth(source.visibleRows)', 'adjusts widths of selected columns on source sheet'),
        Command('g%', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = float', 'sets type of selected columns to float'),
        Command('g#', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = int', 'sets type of selected columns to int'),
        Command('g@', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = date', 'sets type of selected columns to date'),
        Command('g$', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = currency', 'sets type of selected columns to currency'),
        Command('g~', 'for c in selectedRows or source.nonKeyVisibleCols: c.type = str', 'sets type of selected columns to str'),
    ]

ColumnsSheet.columns += [
        ColumnAttr('expr'),
    ]

#### slicing and dicing
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
        self.nKeys = sheets[0].nKeys

        rowsBySheetKey = {}
        rowsByKey = {}

        with Progress(self, total=sum(len(vs.rows) for vs in sheets)*2) as prog:
            for vs in sheets:
                rowsBySheetKey[vs] = {}
                for r in vs.rows:
                    prog.addProgress(1)
                    key = tuple(c.getTypedValue(r) for c in vs.keyCols)
                    rowsBySheetKey[vs][key] = r

            for sheetnum, vs in enumerate(sheets):
                # subsequent elements are the rows from each source, in order of the source sheets
                for c in vs.keyCols:
                    self.addColumn(SubrowColumn(c, sheetnum+1))
                for r in vs.rows:
                    prog.addProgress(1)
                    key = tuple(c.getTypedValue(r) for c in vs.keyCols)
                    if key not in rowsByKey:
                        rowsByKey[key] = [key] + [rowsBySheetKey[vs2].get(key) for vs2 in sheets]  # combinedRow

        self.rows = []

        with Progress(self, len(rowsByKey)) as prog:
            for k, combinedRow in rowsByKey.items():
                prog.addProgress(1)

                if self.jointype == 'full':  # keep all rows from all sheets
                    self.addRow(combinedRow)

                elif self.jointype == 'inner':  # only rows with matching key on all sheets
                    if all(combinedRow):
                        self.addRow(combinedRow)

                elif self.jointype == 'outer':  # all rows from first sheet
                    if combinedRow[1]:
                        self.addRow(combinedRow)

                elif self.jointype == 'diff':  # only rows without matching key on all sheets
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
