import collections

from visidata import globalCommand, BaseSheet, Column, options, vd, anytype, ENTER, asyncthread, Sheet, IndexSheet
from visidata import CellColorizer, RowColorizer, JsonLinesSheet, AttrDict
from visidata import ColumnAttr, ColumnItem
from visidata import TsvSheet, Path, Option
from visidata import undoAttrFunc, VisiData, vlen

vd.option('visibility', 0, 'visibility level (0=low, 1=high)')

vd_system_sep = '\t'


@BaseSheet.lazy_property
def optionsSheet(sheet):
    return OptionsSheet(sheet.name+"_options", source=sheet)

@VisiData.lazy_property
def globalOptionsSheet(vd):
    return OptionsSheet('global_options', source='global')


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
            ColumnAttr('name'),
            ColumnAttr('keycol', type=int, width=0),
            ColumnAttr('width', type=int),
            ColumnAttr('height', type=int),
            ColumnAttr('hoffset', type=int, width=0),
            ColumnAttr('voffset', type=int, width=0),
            ColumnAttr('type', 'typestr'),
            ColumnAttr('fmtstr'),
            ColumnAttr('formatter'),
            ValueColumn('value'),
            ColumnAttr('expr'),
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
        Column('option', getter=lambda col,row: row.name),
        Column('value',
            getter=lambda col,row: col.sheet.diffOption(row.name),
            setter=lambda col,row,val: options.set(row.name, val, col.sheet.source),
            ),
        Column('default', getter=lambda col,row: options.getdefault(row.name)),
        Column('description', width=40, getter=lambda col,row: options._get(row.name, 'default').helpstr),
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
        self.columns[1].name = 'global_value' if self.source == 'global' else 'sheet_value'


vd._lastInputs = collections.defaultdict(dict)  # [input_type] -> {'input': anything}

class LastInputsSheet(JsonLinesSheet):
    columns = [
        ColumnItem('type'),
        ColumnItem('input'),
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colnames = {col.name:col for col in self.columns}

    def addRow(self, row, **kwargs):
        'Update lastInputs before adding row.'
        row = AttrDict(row)
        if row.input in vd._lastInputs[row.type]:
            del vd._lastInputs[row.type][row.input]  # so will be added as last entry
        vd._lastInputs[row.type][row.input] = 1
        return super().addRow(row, **kwargs)

    def appendRow(self, row):
        'Append *row* (AttrDict with *type* and *input*) directly to source.'
        hist = self.history(row.type)
        if hist and hist[-1] == row.input:
            return

        self.addRow(row)

        if self.source:
            with self.source.open_text(mode='a', encoding=self.options.encoding) as fp:
                import json
                fp.write(json.dumps(row) + '\n')

    def history(self, t):
        'Return list of inputs in category *t*, with last element being the most recently added.'
        return list(vd._lastInputs[t].keys())


@VisiData.lazy_property
def lastInputsSheet(vd):
    name = options.input_history

    if not name:
        return LastInputsSheet('last_inputs', source=None, rows=[])

    p = Path(name)
    if not p.is_absolute():
        p = Path(options.visidata_dir)/f'{name}.jsonl'

    vs = LastInputsSheet(name, source=p)
    try:
        vs.reload.__wrapped__(vs)
    except FileNotFoundError:
        pass

    return vs


@VisiData.property
def allColumnsSheet(vd):
    return ColumnsSheet("all_columns", source=vd.stackedSheets)

@VisiData.api
def save_visidatarc(vd, p, vs):
    with p.open_text(mode='w') as fp:
        for optname, val in sorted(vd.options.getall().items()):
            rval = repr(val)
            defopt = vd.options._get(optname, 'default')
            leading = '# ' if val == defopt.value else ''
            fp.write(f'{leading}options.{optname:25s} = {rval:10s}  # {defopt.helpstr}\n')


@ColumnsSheet.command('&', 'join-cols', 'add column from concatenating selected source columns')
def join_cols(sheet):
    cols = sheet.onlySelectedRows
    destSheet = cols[0].sheet

    if len(set(c.sheet for c in cols)) > 1:
        vd.fail('joined columns must come from the same source sheet')

    c = Column(options.name_joiner.join(c.name for c in cols),
                getter=lambda col,row,cols=cols,ch=options.value_joiner: ch.join(c.getDisplayValue(row) for c in cols))

    vd.status(f"added {c.name} to {destSheet}")
    destSheet.addColumn(c, index=sheet.cursorRowIndex)


# copy vd.sheets so that ColumnsSheet itself isn't included (for recalc in addRow)
globalCommand('gC', 'columns-all', 'vd.push(vd.allColumnsSheet)', 'open Columns Sheet: edit column properties for all visible columns from all sheets on the sheets stack')
globalCommand('O', 'options-global', 'vd.push(vd.globalOptionsSheet)', 'open Options Sheet: edit global options (apply to all sheets)')

BaseSheet.addCommand('zO', 'options-sheet', 'vd.push(sheet.optionsSheet)', 'open Options Sheet: edit sheet options (apply to current sheet only)')
BaseSheet.addCommand(None, 'open-inputs', 'vd.push(lastInputsSheet)', '')

Sheet.addCommand('C', 'columns-sheet', 'vd.push(ColumnsSheet(name+"_columns", source=[sheet]))', 'open Columns Sheet: edit column properties for current sheet')

# used ColumnsSheet, affecting the 'row' (source column)
ColumnsSheet.addCommand('g!', 'key-selected', 'for c in onlySelectedRows: c.sheet.setKeys([c])', 'toggle selected rows as key columns on source sheet')
ColumnsSheet.addCommand('gz!', 'key-off-selected', 'for c in onlySelectedRows: c.sheet.unsetKeys([c])', 'unset selected rows as key columns on source sheet')

ColumnsSheet.addCommand('g-', 'hide-selected', 'onlySelectedRows.hide()', 'hide selected columns on source sheet')
ColumnsSheet.addCommand(None, 'resize-source-rows-max', 'for c in selectedRows or [cursorRow]: c.setWidth(c.getMaxWidth(c.sheet.visibleRows))', 'adjust widths of selected source columns')

ColumnsSheet.addCommand('g%', 'type-float-selected', 'onlySelectedRows.type=float', 'set type of selected columns to float')
ColumnsSheet.addCommand('g#', 'type-int-selected', 'onlySelectedRows.type=int', 'set type of selected columns to int')
ColumnsSheet.addCommand('gz#', 'type-len-selected', 'onlySelectedRows.type=vlen', 'set type of selected columns to len')
ColumnsSheet.addCommand('g@', 'type-date-selected', 'onlySelectedRows.type=date', 'set type of selected columns to date')
ColumnsSheet.addCommand('g$', 'type-currency-selected', 'onlySelectedRows.type=currency', 'set type of selected columns to currency')
ColumnsSheet.addCommand('g~', 'type-string-selected', 'onlySelectedRows.type=str', 'set type of selected columns to str')
ColumnsSheet.addCommand('gz~', 'type-any-selected', 'onlySelectedRows.type=anytype', 'set type of selected columns to anytype')
ColumnsSheet.addCommand('gz%', 'type-floatsi-selected', 'onlySelectedRows.type=floatsi', 'set type of selected columns to floatsi')
ColumnsSheet.addCommand('', 'type-floatlocale-selected', 'onlySelectedRows.type=floatlocale', 'set type of selected columns to float using system locale')

OptionsSheet.addCommand('d', 'unset-option', 'options.unset(cursorRow.name, str(source))', 'remove option override for this context')
OptionsSheet.addCommand(None, 'edit-option', 'editOption(cursorRow)', 'edit option at current row')
OptionsSheet.bindkey('e', 'edit-option')
OptionsSheet.bindkey(ENTER, 'edit-option')
MetaSheet.class_options.header = 0


vd.addGlobals({
    'ColumnsSheet': ColumnsSheet,
    'MetaSheet': MetaSheet,
    'OptionsSheet': OptionsSheet,
    'VisiDataMetaSheet': VisiDataMetaSheet,
})
