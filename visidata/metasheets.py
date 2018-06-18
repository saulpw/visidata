import collections
import itertools

from visidata import globalCommand, Sheet, Column, options, Colorizer, Command, vd, error, anytype, ENTER, async, status, Progress
from visidata import ColumnAttr, ColumnEnum, ColumnItem, DescribeSheet, ColumnExpr, SubrowColumn
from visidata import getGlobals

globalCommand('gC', 'vd.push(ColumnsSheet("all_columns", source=vd.sheets))', 'open Columns Sheet with all columns from all sheets', 'meta-columns-all'),
globalCommand('S', 'vd.push(vd.sheetsSheet)', 'open Sheets Sheet', 'meta-sheets')
globalCommand('gS', 'vd.push(SheetsSheet("all_sheets", source=list(vd.allSheets.keys())))', 'open global Sheets Sheet', 'meta-sheets-all')
globalCommand('O', 'vd.push(vd.optionsSheet)', 'open Options', 'meta-options')

globalCommand('zKEY_F(1)', 'vd.push(HelpSheet(name + "_commands", source=sheet))', 'view sheet of commands and keybindings', 'meta-commands')

Sheet.commands += [
    Command('C', 'vd.push(ColumnsSheet(sheet.name+"_columns", source=sheet))', 'open Columns Sheet', 'meta-columns-sheet'),
]


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
            ColumnAttr('sheet'),
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
    commands = [
        Command('column-source-width-max', 'for c in selectedRows or [cursorRow]: c.width = c.getMaxWidth(source.visibleRows)', 'adjust widths of selected source columns'),
        Command('&', 'rows.insert(cursorRowIndex, combineColumns(selectedRows or error("no columns selected to concatenate")))', 'add column from concatenating selected source columns'),
    ]
    def reload(self):
        if isinstance(self.source, Sheet):
            self.rows = self.source.columns
            self.cursorRowIndex = self.source.cursorColIndex
            self.columns[0].hide()  # hide 'sheet' column if only one sheet
        elif isinstance(self.source, list):  # lists of Columns
            self.rows = []
            for src in self.source:
                if src is not self:
                    self.rows.extend(src.columns)

class SheetsSheet(Sheet):
    rowtype = 'sheets'
    precious = False
    commands = [
        Command(ENTER, 'vd.push(cursorRow)', 'jump to sheet referenced in current row'),
        Command('g'+ENTER, 'for vs in selectedRows: vd.push(vs)', 'push selected sheets to top of sheets stack'),
        Command('g^R', 'for vs in selectedRows or rows: vs.reload()', 'reload all selected sheets', 'reload-all'),
        Command('&', 'vd.replace(createJoinedSheet(selectedRows or error("no sheets selected to join"), jointype=chooseOne(jointypes)))', 'merge the selected sheets with visible columns from all, keeping rows according to jointype', 'sheet-join'),
        Command('gC', 'vd.push(ColumnsSheet("all_columns", source=selectedRows or rows[1:]))', 'open Columns Sheet with all columns from selected sheets', 'sheet-columns-selected'),
    ]
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
    commands = [
        Command(ENTER, 'editOption(cursorRow)', 'edit option', 'set-row-input'),
        Command('e', 'set-row-input')
    ]
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
            self.source.set(row.name, not row.value)
        else:
            self.source.set(row.name, self.editCell(1))

    def reload(self):
        self.rows = list(self.source._opts.values())

vd().optionsSheet = OptionsSheet('options', source=options)
vd().sheetsSheet = SheetsSheet("sheets", source=vd().sheets)

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
columnCommands = [
        Command('g!', 'for c in selectedRows or [cursorRow]: c.sheet.toggleKeyColumn(c)', 'toggle selected rows as key columns on source sheet'),
        Command('gz!', 'for c in selectedRows or [cursorRow]: c.sheet.keyCols.remove(c)', 'unset selected rows as key columns on source sheet'),
        Command('g-', 'for c in selectedRows or [cursorRow]: c.hide()', 'hide selected source columns on source sheet'),
        Command('g%', 'for c in selectedRows or [cursorRow]: c.type = float', 'set type of selected source columns to float'),
        Command('g#', 'for c in selectedRows or [cursorRow]: c.type = int', 'set type of selected source columns to int'),
        Command('g@', 'for c in selectedRows or [cursorRow]: c.type = date', 'set type of selected source columns to date'),
        Command('g$', 'for c in selectedRows or [cursorRow]: c.type = currency', 'set type of selected columns to currency'),
        Command('g~', 'for c in selectedRows or [cursorRow]: c.type = str', 'set type of selected columns to str'),
        Command('gz~', 'for c in selectedRows or [cursorRow]: c.type = anytype', 'set type of selected columns to anytype'),
    ]

ColumnsSheet.commands += columnCommands
DescribeSheet.commands += columnCommands


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
