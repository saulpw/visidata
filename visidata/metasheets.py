import collections
import itertools

from visidata import globalCommand, Sheet, Column, options, Colorizer, Command, vd, error, anytype, ENTER, asyncthread, status, Progress
from visidata import ColumnAttr, ColumnEnum, ColumnItem, ColumnExpr, SubrowColumn
from visidata import getGlobals

globalCommand('gC', 'columns-all', 'vd.push(ColumnsSheet("all_columns", source=vd.sheets))')
globalCommand('S', 'sheets', 'vd.push(vd.sheetsSheet)')
globalCommand('gS', 'sheets-graveyard', 'vd.push(vd.graveyardSheet).reload()')
globalCommand('O', 'options', 'vd.push(vd.optionsSheet)')
globalCommand('zKEY_F(1)', 'help-commands', 'vd.push(HelpSheet(name + "_commands", source=sheet))')

Sheet.addCommand('C', 'columns-sheet', 'vd.push(ColumnsSheet(sheet.name+"_columns", source=[sheet]))')


class ColumnsSheet(Sheet):
    rowtype = 'columns'
    precious = False
    class ValueColumn(Column):
        'passthrough to the value on the source cursorRow'
        def calcValue(self, srcCol):
            return srcCol.getDisplayValue(srcCol.sheet.cursorRow)
        def setValue(self, srcCol, val):
            srcCol.setValue(self.sheet.source.cursorRow, val)

    columns = [
            ColumnAttr('sheet', type=str),
            ColumnAttr('name', width=options.default_width),
            ColumnAttr('width', type=int),
            ColumnEnum('type', getGlobals(), default=anytype),
            ColumnAttr('fmtstr'),
            ValueColumn('value', width=options.default_width),
            ColumnAttr('expr'),
    ]
    nKeys = 2
    colorizers = Sheet.colorizers + [
            Colorizer('row', 7, lambda self,c,r,v: options.color_key_col if r in r.sheet.keyCols else None),
            Colorizer('row', 6, lambda self,c,r,v: options.color_hidden_col if r.hidden else None),
    ]
    def reload(self):
        if len(self.source) == 1:
            self.rows = self.source[0].columns
            self.cursorRowIndex = self.source[0].cursorColIndex
            self.columns[0].hide()  # hide 'sheet' column if only one sheet
        else:
            self.rows = [col for vs in self.source for col in vs.visibleCols if vs is not self]

ColumnsSheet.addCommand(None, 'resize-source-rows-max', 'for c in selectedRows or [cursorRow]: c.width = c.getMaxWidth(source.visibleRows)')
ColumnsSheet.addCommand('&', 'join-cols', 'rows.insert(cursorRowIndex, combineColumns(selectedRows or error("no columns selected to concatenate")))')


class SheetsSheet(Sheet):
    rowtype = 'sheets'
    precious = False
    columns = [
        ColumnAttr('name', width=30),
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
        ColumnAttr('nVisibleCols', type=int),
        ColumnAttr('cursorDisplay'),
        ColumnAttr('keyColNames'),
        ColumnAttr('source'),
        ColumnAttr('progressPct'),
    ]
    nKeys = 1

    def newRow(self):
        return Sheet('', columns=[ColumnItem('', 0)], rows=[])

    def reload(self):
        self.rows = self.source

SheetsSheet.addCommand(ENTER, 'open-row', 'dest=cursorRow; vd.sheets.remove(sheet) if not sheet.precious else None; vd.push(dest)')
SheetsSheet.addCommand('g'+ENTER, 'open-rows', 'for vs in selectedRows: vd.push(vs)')
SheetsSheet.addCommand('g^R', 'reload-selected', 'for vs in selectedRows or rows: vs.reload()')
SheetsSheet.addCommand('&', 'join-sheets', 'vd.replace(createJoinedSheet(selectedRows or error("no sheets selected to join"), jointype=chooseOne(jointypes)))')
SheetsSheet.addCommand('gC', 'columns-selected', 'vd.push(ColumnsSheet("all_columns", source=selectedRows or rows[1:]))')
SheetsSheet.addCommand('gI', 'describe-selected', 'vd.push(DescribeSheet("describe_all", source=selectedRows or rows[1:]))')

# source: vd.allSheets (with BaseSheet as weakref keys)
class GraveyardSheet(SheetsSheet):
    rowtype = 'dead sheets'  # rowdef: BaseSheet
    def reload(self):
        self.rows = list(vs for vs in self.source.keys() if vs not in vd().sheets)


class HelpSheet(Sheet):
    'Show all commands available to the source sheet.'
    rowtype = 'commands'
    precious = False

    class HelpColumn(Column):
        def calcValue(self, r):
            cmd = self.sheet.source.getCommand(self.prefix+r.name, None)
            return cmd.helpstr if cmd else '-'

    columns = [
        ColumnAttr('keystrokes', 'name'),
        ColumnAttr('helpstr'),
        HelpColumn('with_g_prefix', prefix='g'),
        HelpColumn('with_z_prefix', prefix='z'),
        ColumnAttr('execstr', width=0),
    ]
    nKeys = 1
    def reload(self):
        self.rows = []
        for src in self.source._commands.maps:
            self.rows.extend(src.values())

class OptionsSheet(Sheet):
    rowtype = 'options'
    precious = False
    columns = (ColumnAttr('option', 'name'),
               ColumnAttr('value'),
               ColumnAttr('default'),
               ColumnAttr('helpstr'))
    colorizers = Sheet.colorizers + [
        Colorizer('cell', 9, lambda s,c,r,v: v.value if c.name in ['value', 'default'] and r.name.startswith('color_') else None)
    ]

    nKeys = 1

    def editOption(self, row):
        if isinstance(row.default, bool):
            options[row.name] = not row.value
        else:
            options[row.name] = self.editCell(1)

    def reload(self):
        self.rows = list(self.source._opts.values())

OptionsSheet.addCommand(ENTER, 'edit-row', 'editOption(cursorRow)')
OptionsSheet.bindkey('e', 'edit-row')

vd().optionsSheet = OptionsSheet('options', source=options)
vd().sheetsSheet = SheetsSheet("sheets", source=vd().sheets)
vd().graveyardSheet = GraveyardSheet("sheets_graveyard", source=vd().allSheets)


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

# used ColumnsSheet, affecting the 'row' (source column)
ColumnsSheet.addCommand('g!', 'key-selected', 'for c in selectedRows or [cursorRow]: c.sheet.toggleKeyColumn(c)')
ColumnsSheet.addCommand('gz!', 'key-off-selected', 'for c in selectedRows or [cursorRow]: c.sheet.keyCols.remove(c)')
ColumnsSheet.addCommand('g-', 'hide-selected', 'for c in selectedRows or [cursorRow]: c.hide()')
ColumnsSheet.addCommand('g%', 'type-float-selected', 'for c in selectedRows or [cursorRow]: c.type = float')
ColumnsSheet.addCommand('g#', 'type-int-selected', 'for c in selectedRows or [cursorRow]: c.type = int')
ColumnsSheet.addCommand('g@', 'type-date-selected', 'for c in selectedRows or [cursorRow]: c.type = date')
ColumnsSheet.addCommand('g$', 'type-currency-selected', 'for c in selectedRows or [cursorRow]: c.type = currency')
ColumnsSheet.addCommand('g~', 'type-string-selected', 'for c in selectedRows or [cursorRow]: c.type = str')
ColumnsSheet.addCommand('gz~', 'type-any-selected', 'for c in selectedRows or [cursorRow]: c.type = anytype')


#### slicing and dicing
# rowdef: [(key, ...), sheet1_row, sheet2_row, ...]
#   if a sheet does not have this key, sheet#_row is None
class SheetJoin(Sheet):
    'Column-wise join/merge. `jointype` constructor arg should be one of jointypes.'

    @asyncthread
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
                    key = tuple(c.getDisplayValue(r) for c in vs.keyCols)
                    rowsBySheetKey[vs][key].append(r)

            for sheetnum, vs in enumerate(sheets):
                # subsequent elements are the rows from each source, in order of the source sheets
                for c in vs.nonKeyVisibleCols:
                    self.addColumn(SubrowColumn(c, sheetnum+1))
                for r in vs.rows:
                    prog.addProgress(1)
                    key = tuple(c.getDisplayValue(r) for c in vs.keyCols)
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
