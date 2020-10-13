from visidata import globalCommand, BaseSheet, Column, options, vd, anytype, ENTER, asyncthread, option, Sheet, IndexSheet
from visidata import CellColorizer, RowColorizer
from visidata import ColumnAttr, ColumnEnum, ColumnItem
from visidata import TsvSheet, Path, Option
from visidata import undoAttrFunc, VisiData, vlen

option('visibility', 0, 'visibility level (0=low, 1=high)')

vd_system_sep = '\t'


@BaseSheet.lazy_property
def optionsSheet(sheet):
    return OptionsSheet(sheet.name+"_options", source=sheet)

@VisiData.lazy_property
def globalOptionsSheet(vd):
    return OptionsSheet('global_options', source='override')


class ColumnsSheet(Sheet):
    rowtype = 'columns'
    _rowtype = Column
    _coltype = ColumnAttr
    precious = False
    class ValueColumn(Column):
        'passthrough to the value on the source cursorRow'
        def calcValue(self, srcCol):
            return srcCol.getDisplayValue(srcCol.sheet.cursorRow)
        def setValue(self, srcCol, val):
            srcCol.setValue(srcCol.sheet.cursorRow, val)

    columns = [
            ColumnAttr('sheet', type=str),
            ColumnAttr('name', width=options.default_width),
            ColumnAttr('width', type=int),
            ColumnAttr('height', type=int),
            ColumnAttr('hoffset', type=int, width=0),
            ColumnAttr('voffset', type=int, width=0),
            ColumnEnum('type', vd.getGlobals(), default=anytype),
            ColumnAttr('fmtstr'),
            ValueColumn('value', width=options.default_width),
            Column('expr', getter=lambda col,row: getattr(row, 'expr', ''),
                           setter=lambda col,row,val: setattr(row, 'expr', val)),
            ColumnAttr('ncalcs', type=int, width=0, cache=False),
            ColumnAttr('maxtime', type=float, width=0, cache=False),
            ColumnAttr('totaltime', type=float, width=0, cache=False),
    ]
    nKeys = 2
    colorizers = [
        RowColorizer(7, 'color_key_col', lambda s,c,r,v: r and r.keycol),
        RowColorizer(8, 'color_hidden_col', lambda s,c,r,v: r and r.hidden),
    ]
    def reload(self):
        if len(self.source) == 1:
            self.rows = self.source[0].columns
            self.cursorRowIndex = self.source[0].cursorColIndex
            self.columns[0].hide()  # hide 'sheet' column if only one sheet
        else:
            self.rows = [col for vs in self.source for col in vs.visibleCols if vs is not self]

    def newRow(self):
        c = type(self.source[0])._coltype()
        c.recalc(self.source[0])
        return c

class MetaSheet(Sheet):
    pass

class VisiDataMetaSheet(TsvSheet):
    pass

# commandline must not override these for internal sheets
VisiDataMetaSheet.class_options.delimiter = vd_system_sep
VisiDataMetaSheet.class_options.header = 1
VisiDataMetaSheet.class_options.skip = 0
VisiDataMetaSheet.class_options.row_delimiter = '\n'
VisiDataMetaSheet.class_options.encoding = 'utf-8'


class OptionsSheet(Sheet):
    _rowtype = Option  # rowdef: Option
    rowtype = 'options'
    precious = False
    columns = (
        ColumnAttr('option', 'name'),
        Column('value',
            getter=lambda col,row: col.sheet.diffOption(row.name),
            setter=lambda col,row,val: options.set(row.name, val, col.sheet.source),
            ),
        Column('default', getter=lambda col,row: options.getdefault(row.name)),
        Column('description', width=40, getter=lambda col,row: options._get(row.name, 'global').helpstr),
        ColumnAttr('replayable'),
    )
    colorizers = [
        CellColorizer(3, None, lambda s,c,r,v: v.value if r and c in s.columns[1:3] and r.name.startswith('color_') else None),
    ]
    nKeys = 1

    def diffOption(self, optname):
        return options.getonly(optname, self.source, '')

    def editOption(self, row):
        currentValue = options.getobj(row.name, self.source)
        vd.addUndo(options.set, row.name, currentValue, self.source)
        if isinstance(row.value, bool):
            options.set(row.name, not currentValue, self.source)
        else:
            options.set(row.name, self.editCell(1, value=currentValue), self.source)

    def reload(self):
        self.rows = []
        for k in options.keys():
            opt = options._get(k)
            self.addRow(opt)
        self.columns[1].name = 'global_value' if self.source == 'override' else 'sheet_value'


class VisiDataSheet(IndexSheet):
    rowtype = 'metasheets'
    precious = False
    columns = [
        ColumnAttr('items', 'nRows', type=int),
        ColumnAttr('name', width=0),
        ColumnAttr('description', width=50),
        ColumnAttr('command', 'longname', width=0),
        ColumnAttr('shortcut', 'shortcut_en', width=11),
    ]
    nKeys = 0

    def reload(self):
        self.rows = []
        for vdattr, sheetname, longname, shortcut, desc in [
            ('currentDirSheet', '.', 'open-dir-current', '', 'DirSheet for the current directory'),
            ('sheetsSheet', 'sheets', 'sheets-stack', 'Shift+S', 'current sheet stack'),
            ('allSheetsSheet', 'sheets_all', 'sheets-all', 'g Shift+S', 'all sheets this session'),
            ('allColumnsSheet', 'all_columns', 'columns-all', 'g Shift+C', 'all columns from all sheets'),
            ('cmdlog', 'cmdlog', 'cmdlog-all', 'g Shift+D', 'log of all commands this session'),
            ('globalOptionsSheet', 'options_global', 'open-global', 'Shift+O', 'default option values applying to every sheet'),
            ('recentErrorsSheet', 'errors', 'open-errors', 'Ctrl+E', 'stacktrace of most recent error'),
            ('statusHistorySheet', 'statuses', 'open-statuses', 'Ctrl+P', 'status messages from current session'),
            ('threadsSheet', 'threads', 'open-threads', 'Ctrl+T', 'threads and profiling'),
            ('vdmenu', 'visidata_menu', 'open-vd', 'Shift+V', 'VisiData menu (this sheet)'),
            ('pluginsSheet', 'plugins', 'open-plugins', '', 'VisiData community plugins'),
            ]:
            vs = getattr(vd, vdattr)
            vs.description = desc
            vs.shortcut_en = shortcut
            vs.longname = longname
            if vs is not self:
                vs.ensureLoaded()
            self.addRow(vs)


@VisiData.lazy_property
def vdmenu(vd):
    return VisiDataSheet('visidata_menu', source=vd)

@VisiData.property
def allColumnsSheet(vd):
    return ColumnsSheet("all_columns", source=list(vd.sheets))


@ColumnsSheet.command('&', 'join-cols', 'add column from concatenating selected source columns')
def join_cols(sheet):
    cols = sheet.someSelectedRows
    destSheet = cols[0].sheet

    if len(set(c.sheet for c in cols)) > 1:
        vd.fail('joined columns must come from the same source sheet')

    c = Column(options.name_joiner.join(c.name for c in cols),
                getter=lambda col,row,cols=cols,ch=options.value_joiner: ch.join(c.getDisplayValue(row) for c in cols))

    vd.status(f"added {c.name} to {destSheet}")
    destSheet.addColumn(c, index=sheet.cursorRowIndex)


# copy vd.sheets so that ColumnsSheet itself isn't included (for recalc in addRow)
globalCommand('gC', 'columns-all', 'vd.push(vd.allColumnsSheet)', 'open Columns Sheet: edit column properties for all visible columns from all sheets')
globalCommand('O', 'options-global', 'vd.push(vd.globalOptionsSheet)', 'open Options Sheet: edit global options (apply to all sheets)')

BaseSheet.addCommand('V', 'open-vd', 'vd.push(vd.vdmenu)', 'open VisiData menu: browse list of core sheets')
BaseSheet.addCommand('zO', 'options-sheet', 'vd.push(sheet.optionsSheet)', 'open Options Sheet: edit sheet options (apply to current sheet only)')

Sheet.addCommand('C', 'columns-sheet', 'vd.push(ColumnsSheet(name+"_columns", source=[sheet]))', 'open Columns Sheet: edit column properties for current sheet')

# used ColumnsSheet, affecting the 'row' (source column)
ColumnsSheet.addCommand('g!', 'key-selected', 'for c in someSelectedRows: c.sheet.setKeys([c])', 'toggle selected rows as key columns on source sheet')
ColumnsSheet.addCommand('gz!', 'key-off-selected', 'for c in someSelectedRows: c.sheet.unsetKeys([c])', 'unset selected rows as key columns on source sheet')

ColumnsSheet.addCommand('g-', 'hide-selected', 'someSelectedRows.hide()', 'hide selected columns on source sheet')
ColumnsSheet.addCommand(None, 'resize-source-rows-max', 'for c in selectedRows or [cursorRow]: c.setWidth(c.getMaxWidth(c.sheet.visibleRows))', 'adjust widths of selected source columns')

ColumnsSheet.addCommand('g%', 'type-float-selected', 'someSelectedRows.type=float', 'set type of selected columns to float')
ColumnsSheet.addCommand('g#', 'type-int-selected', 'someSelectedRows.type=int', 'set type of selected columns to int')
ColumnsSheet.addCommand('gz#', 'type-len-selected', 'someSelectedRows.type=vlen', 'set type of selected columns to len')
ColumnsSheet.addCommand('g@', 'type-date-selected', 'someSelectedRows.type=date', 'set type of selected columns to date')
ColumnsSheet.addCommand('g$', 'type-currency-selected', 'someSelectedRows.type=currency', 'set type of selected columns to currency')
ColumnsSheet.addCommand('g~', 'type-string-selected', 'someSelectedRows.type=str', 'set type of selected columns to str')
ColumnsSheet.addCommand('gz~', 'type-any-selected', 'someSelectedRows.type=anytype', 'set type of selected columns to anytype')

OptionsSheet.addCommand(None, 'edit-option', 'editOption(cursorRow)', 'edit option at current row')
OptionsSheet.bindkey('e', 'edit-option')
OptionsSheet.bindkey(ENTER, 'edit-option')
MetaSheet.class_options.header = 0
