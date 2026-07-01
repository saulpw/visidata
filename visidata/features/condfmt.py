'''Conditional formatting commands.  #3061'''

from visidata import vd, Sheet, CellColorizer, RowColorizer, ColumnColorizer


# default colors offered when adding a conditional format
condfmt_default_colors = [
    'red', 'green', 'yellow', 'cyan', 'magenta', 'blue',
    'on red', 'on green', 'on yellow', 'on cyan', 'on magenta', 'on blue',
]

condfmt_precedence = 8


vd.help_condfmt_expr = '''# Conditional Format Expression

A Python expression evaluated against each cell.  Color is applied where the expression is truthy.

## Bindings

- bare column names resolve to that column's typed value for the current row (e.g. `temperature > 100` on a sheet with a `temperature` column)
- `value` / `v` -- the typed value of the current cell
- `sheet` / `s`, `col` / `c`, `row` / `r` -- the sheet, column, and row

## Examples

    value < 0
    score >= 90
    status == 'failed'
    'error' in value
    c.name.startswith('total_')

## Notes

- Row colorizers fire per cell, so `value` refers to the current cell, not "the row's value".  For row-level rules, reference a sibling column by name (e.g. `status == 'failed'`).
- Cells where the expression raises are silently not colored.  Run vd with `--debug` to see exceptions in the status log.
'''


vd.help_condfmt_color = '''# Conditional Format Color

A color string or a `color_*` option name.

## Color syntax

    <attribute> <fg-color> on <bg-color>

- attributes: [:bold]bold[/] [:underline]underline[/] [:italic]italic[/] [:reverse]reverse[/]
- colors: 0-255 or [:black on 238]black[/] [:red on 238]red[/] [:green on 238]green[/] [:yellow on 238]yellow[/] [:blue on 238]blue[/] [:magenta on 238]magenta[/] [:cyan on 238]cyan[/] [:white on 238]white[/]
- a second color is used as a fallback if the first is not available

## Color option name

Any `color_*` option name works as a synonym, with or without the `color_` prefix -- the conditional format picks up whatever the active theme defines:

- `error` -> `color_error`
- `current_row`, `selected_row`, `key_col`, ...

## Examples

    red
    bold green
    on red
    215 yellow on 17
    error

See [:onclick https://visidata.org/docs/colors]https://visidata.org/docs/colors[/] for more detail.
'''


class CondFmtContext(dict):
    '''Eval-context for conditional formatting expressions.

    Exposes the four colorizer arguments under both short (s/c/r/v) and
    long (sheet/col/row/value) names, and falls back to bare column-name
    lookups for the current row -- like `addcol-expr` and friends.

    Note: this duplicates a bit of LazyComputeRow's bare-column-name
    resolution rather than calling Sheet.evalExpr, because LCR's `_lcm`
    is cached on col/sheet and would pin the first LCR's `extra` AttrDict
    across calls -- so cell-specific bindings (`value`, `v`) would leak
    between cells.  See sheets.py:91-95.
    '''
    def __init__(self, sheet, col, row, value):
        super().__init__(s=sheet, sheet=sheet,
                         c=col, col=col,
                         r=row, row=row,
                         v=value, value=value)
        self._sheet = sheet
        self._row = row

    def __missing__(self, k):
        col = self._sheet.colsByName.get(k)
        if col is not None:
            return col.getTypedValue(self._row)
        raise KeyError(k)


@Sheet.api
def pick_unused_color(sheet):
    'Return the first default conditional-format color not already used by a colorizer on this sheet.'
    used = {cz.coloropt for cz in sheet._colorizers if cz.coloropt}
    for c in condfmt_default_colors:
        if c not in used:
            return c
    return condfmt_default_colors[0]


def _make_color_func(expr):
    'Compile *expr* once and return a Colorizer func evaluated against a CondFmtContext.'
    code = compile(expr, '<color expr>', 'eval')
    def func(s, c, r, v):
        # _colorize passes a DisplayWrapper as v; expressions want the typed value
        typedval = v.typedval if hasattr(v, 'typedval') else v
        try:
            return eval(code, vd.getGlobals(), CondFmtContext(s, c, r, typedval))
        except Exception as e:  # cells where the expr cannot evaluate are simply not colored
            vd.debug(f'condfmt `{expr}`: {type(e).__name__}: {e}')
            return False
    return func


def _add_condfmt(sheet, ColorizerClass, noun, color, expr):
    sheet.addColorizer(ColorizerClass(condfmt_precedence, color, _make_color_func(expr)))
    vd.status(f'{noun} where `{expr}` colored `{color}`')


@Sheet.api
def color_cell(sheet, color, expr):
    'Add a CellColorizer that paints cells with *color* where *expr* is truthy.'
    _add_condfmt(sheet, CellColorizer, 'cells', color, expr)


@Sheet.api
def color_row(sheet, color, expr):
    'Add a RowColorizer that paints rows with *color* where *expr* is truthy.'
    _add_condfmt(sheet, RowColorizer, 'rows', color, expr)


@Sheet.api
def color_col(sheet, color, expr):
    'Add a ColumnColorizer that paints columns with *color* where *expr* is truthy.'
    _add_condfmt(sheet, ColumnColorizer, 'columns', color, expr)


@Sheet.api
def inputCondFmt(sheet):
    'Prompt for color and condition expression for conditional formatting.'
    return vd.inputMultiple(
        expr=dict(prompt='expr: ',  type='expr',  help=vd.help_condfmt_expr),
        color=dict(prompt='color: ', value=sheet.pick_unused_color(), help=vd.help_condfmt_color),
    )


Sheet.addCommand('', 'color-cell', 'color_cell(**inputCondFmt())', 'apply color to cells where Python expr is truthy')
Sheet.addCommand('', 'color-row',  'color_row(**inputCondFmt())',  'apply color to rows where Python expr is truthy')
Sheet.addCommand('', 'color-col',  'color_col(**inputCondFmt())',  'apply color to columns where Python expr is truthy')

vd.addMenuItems('''
    View > Color > cells where > color-cell
    View > Color > rows where > color-row
    View > Color > columns where > color-col
''')


## tests

def _condfmt_test_sheet():
    'Build a tiny TableSheet with typed columns for condfmt tests.'
    from visidata import Sheet, Column
    return Sheet('toy', columns=[
        Column('temperature', type=int, getter=lambda c,r: r['temperature']),
        Column('status',      type=str, getter=lambda c,r: r['status']),
    ], rows=[
        {'temperature': 50,  'status': 'ok'},
        {'temperature': 120, 'status': 'failed'},
        {'temperature': -5,  'status': 'cold'},
    ])


def _condfmt_added(sheet):
    'Return colorizers added by condfmt commands (filters by closure qualname).'
    return [c for c in sheet._colorizers
            if getattr(c._func, '__qualname__', '') == '_make_color_func.<locals>.func']


def test_condfmt_bare_column_name(vd):  #3061
    'Bare column names in expressions resolve to the typed value of that column.'
    from visidata import CellColorizer
    s = _condfmt_test_sheet()
    s.color_cell('red', 'temperature > 100')
    cz, = _condfmt_added(s)
    assert isinstance(cz, CellColorizer)
    assert cz.coloropt == 'red'
    assert cz.func(s, s.columns[0], s.rows[0], 50)  is False  # 50 not > 100
    assert cz.func(s, s.columns[0], s.rows[1], 120) is True   # 120 > 100
    assert cz.func(s, s.columns[0], s.rows[2], -5)  is False  # -5 not > 100


def test_condfmt_value_binding(vd):  #3061
    "`value` and `v` resolve to the current cell's typed value."
    s = _condfmt_test_sheet()
    s.color_cell('red', 'value < 0')
    cz, = _condfmt_added(s)
    assert cz.func(s, s.columns[0], s.rows[2], -5) is True
    assert cz.func(s, s.columns[0], s.rows[0], 50) is False

    s = _condfmt_test_sheet()
    s.color_cell('red', 'v < 0')
    cz, = _condfmt_added(s)
    assert cz.func(s, s.columns[0], s.rows[2], -5) is True
    assert cz.func(s, s.columns[0], s.rows[0], 50) is False


def test_condfmt_col_binding(vd):  #3061
    "`c` and `col` resolve to the column being queried, supporting attr access."
    s = _condfmt_test_sheet()
    s.color_col('underline', 'c.name.startswith("temp")')
    cz, = _condfmt_added(s)
    assert cz.func(s, s.columns[0], s.rows[0], 50)    is True   # temperature col
    assert cz.func(s, s.columns[1], s.rows[0], 'ok')  is False  # status col


def test_condfmt_row_binding_string_column(vd):  #3061
    'Row colorizer expression referencing a sibling column by bare name.'
    from visidata import RowColorizer
    s = _condfmt_test_sheet()
    s.color_row('on red', "status == 'failed'")
    cz, = _condfmt_added(s)
    assert isinstance(cz, RowColorizer)
    # row colorizer fires per-cell but truth value is based on the row's status col
    assert cz.func(s, s.columns[0], s.rows[1], 120) is True   # status='failed' row
    assert cz.func(s, s.columns[1], s.rows[1], 'failed') is True
    assert cz.func(s, s.columns[0], s.rows[0], 50)  is False  # status='ok' row


def test_condfmt_silent_eval_error(vd):  #3061
    'Expression errors return False so unrenderable cells are simply not colored.'
    s = _condfmt_test_sheet()
    s.color_cell('red', 'undefined_name > 0')
    cz, = _condfmt_added(s)
    assert cz.func(s, s.columns[0], s.rows[0], 50) is False


def test_pick_unused_color(vd):  #3061
    'pick_unused_color skips colors already in use by colorizers on this sheet.'
    s = _condfmt_test_sheet()
    assert s.pick_unused_color() == 'red'
    s.color_cell('red', '0')
    assert s.pick_unused_color() == 'green'
    s.color_row('green', '0')
    assert s.pick_unused_color() == 'yellow'


def test_condfmt_color_option_name(vd):  #3061
    'A color option name like `error` resolves to that option (color_error).'
    from visidata import colors
    s = _condfmt_test_sheet()
    s.color_cell('error', 'value < 0')  # `error` should resolve to color_error
    cz, = _condfmt_added(s)
    assert cz.coloropt == 'error'  # stored verbatim; resolution happens at draw time
    # colors.get_color('error') falls back to color_error option
    assert colors.get_color('error').colorname == colors.get_color('color_error').colorname


def test_condfmt_value_is_typed_not_wrapper(vd):  #3061
    "`value`/`v` are the typed cell value, not a DisplayWrapper -- so `'a' in value` works."
    s = _condfmt_test_sheet()
    s.color_cell('red', "'a' in value")
    cz, = _condfmt_added(s)
    # invoke through the same call path as draw: _colorize passes a DisplayWrapper
    cellval = s.columns[1].getCell(s.rows[1])  # status='failed' -> contains 'a'
    assert cz.func(s, s.columns[1], s.rows[1], cellval) is True
    cellval = s.columns[1].getCell(s.rows[0])  # status='ok' -> no 'a'
    assert cz.func(s, s.columns[1], s.rows[0], cellval) is False
