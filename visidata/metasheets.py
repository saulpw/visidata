import collections

from visidata import globalCommand, BaseSheet, Column, options, vd, anytype, ENTER, asyncthread, Sheet, IndexSheet
from visidata import CellColorizer, RowColorizer, JsonLinesSheet, AttrDict
from visidata import ColumnAttr, ColumnItem
from visidata import TsvSheet, Path, Option
from visidata import undoAttrFunc, VisiData, vlen

vd.option('visibility', 0, 'visibility level (0=low, 1=high)')

vd_system_sep = '\t'


class ColumnsSheet(Sheet):
    rowtype = 'columns'
    _rowtype = Column
    _coltype = ColumnAttr
    precious = False
    help = '''# Columns Sheet
This is a list of {sheet.nSourceCols} columns on {sheet.displaySource}.
Edit values on this sheet to change the column's appearance on the source sheet.
Edit the _{sheet.cursorCol.name}_ column to {sheet.cursorCol.formatted_help}.

Some column commands can also be done in bulk here, with the `g` prefix:

- `ge` to bulk set the _{sheet.cursorCol.name}_ for all selected "columns"
- `g-` to hide selected "columns"
- `g#` (or any standard type) to set the type of all selected "columns"
{sheet.help_columns}
'''

    class ValueColumn(Column):
        'passthrough to the value on the source cursorRow'
        def calcValue(self, srcCol):
            return srcCol.getDisplayValue(srcCol.sheet.cursorRow)
        def setValue(self, srcCol, val):
            srcCol.setValue(srcCol.sheet.cursorRow, val)

    columns = [
            ColumnAttr('sheet', type=str),
            ColumnAttr('name', help='rename the column on the source sheet'),
            ColumnAttr('keycol', type=int, width=0),
            ColumnAttr('width', type=int, help='set the column width (`0` to hide completely)'),
            ColumnAttr('height', type=int, max_help=1, help='set a maximum height for the row, if this column will fill it'),
            ColumnAttr('hoffset', type=int, width=0),
            ColumnAttr('voffset', type=int, width=0),
            ColumnAttr('type', 'typestr', help='convert all values to a specific type'),
            ColumnAttr('fmtstr', help='use a custom format string, either C-style (`%0.4f`) or Python-style (`{{:0.4f}}`)'),
            ColumnAttr('formatter', max_help=1, help='use a custom format function (**{col.help_formatters}**)'),
            ColumnAttr('displayer', max_help=1, help='use a custom display function (**{col.help_displayers}**)'),
            ValueColumn('value', help='change the value of this cell on the source sheet'),
            ColumnAttr('expr', max_help=1, help='change the main column parameter'),
            ColumnAttr('ncalcs', type=int, width=0, cache=False),
            ColumnAttr('maxtime', type=float, width=0, cache=False),
            ColumnAttr('totaltime', type=float, width=0, cache=False),
    ]
    nKeys = 2
    colorizers = [
        RowColorizer(7, 'color_key_col', lambda s,c,r,v: r and r.keycol),
        RowColorizer(8, 'color_hidden_col', lambda s,c,r,v: r and r.hidden),
    ]

    @property
    def nSourceCols(self):
        return sum(vs.nCols for vs in self.source)

    def loader(self):
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
VisiDataMetaSheet.options.delimiter = vd_system_sep
VisiDataMetaSheet.options.header = 1
VisiDataMetaSheet.options.skip = 0
VisiDataMetaSheet.options.row_delimiter = '\n'
VisiDataMetaSheet.options.encoding = 'utf-8'




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
            with self.source.open(mode='a') as fp:
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
    except Exception as e:
        vd.exceptionCaught(e)

    return vs


@VisiData.property
def allColumnsSheet(vd):
    return ColumnsSheet("all_columns", source=vd.stackedSheets)

@VisiData.api
def save_visidatarc(vd, p, vs):
    with p.open(mode='w') as fp:
        for opt in vs.rows:
            rval = repr(opt.value)
            defopt = vd.options._get(opt.name, 'default')
            leading = '# ' if opt.value == defopt.value else ''
            fp.write(f'{leading}options.{opt.name:25s} = {rval:10s}  # {defopt.helpstr}\n')


ColumnsSheet.addCommand('', 'join-cols', 'sheet.join_cols()', 'add column from concatenating selected source columns')

@ColumnsSheet.api
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

MetaSheet.options.header = 0


vd.addGlobals({
    'ColumnsSheet': ColumnsSheet,
    'MetaSheet': MetaSheet,
    'VisiDataMetaSheet': VisiDataMetaSheet,
})

vd.addMenuItems('''
    View > Columns > this sheet > columns-sheet
    View > Columns > all sheets > columns-all
''')
