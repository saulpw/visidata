# vdsql version history

# 0.2 (2022-10-12)

Added and tested support for these backends:

  - bigquery
  - clickhouse
  - mysql
  - postgres
  - duckdb with `.ddb` extension
  - sqlite with `.sqlite3` extension
  - snowflake support (with unreleased Ibis)

Added options:
- `options.sql_always_count` (default: False), which determines whether to always query
- [freq sheet] histogram available, but by default disabled
   - enable by setting `options.disp_histogram` and `options.disp_histolen`

- set `options.clean_names` to `True` for all ibis sheets
- set `options.load_lazy` to `True` for all ibis sheets
- set `regex_flags` to not ignorecase

- [columns sheet] add `ibis_type`
- [load] provide helpful message if `ibis-framework` dependencies are not installed

Additional commands added:
- `exec-sql` command
- `dup-limit` (keybinding `z"`) and `dup-nolimit` (keybinding `gz"`)

- sidebar keybindings now `b`
    - `zb` to choose sidebar style
    - `b` to toggle instead of cycle
    - `gb` to open sidebar contents in new sheet

Since the last release, most other VisiData commands and features have been implemented to a first degree, to the point that it's easier to talk about what's not implemented, than what is.

VisiData features that don't currently work in vdsql:
 - progress (not possible in many backends)
 - rowcount (disabled by default; is expensive or not possible on some backends)
 - task cancellation

These following commands should be disabled and fail with a warning, instead of erroneously working on the sheet (using only limited data, for example).

Not implemented commands (but probably will be soon/someday):
  - regex select
  - describe-sheet
  - melt
  - freq-summary
  - addcol-capture
  - addcol-incr and addcol-incr-step
  - addcol-window
  - capture-col
  - contract-col
  - expand-col-depth - expand-cols - expand-cols-depth
  - random-rows
  - select-exact-cell - select-exact-row
  - select-rows
  - unselect-expr - select-expr
  - cache-col - cache-cols
  - dive-selected-cells
  - dup-rows - dup-rows-deep - dup-selected-deep
  - data modification commands (pending Ibis support)
    - adding rows or blank columns
    - deleting rows (use select and dup with `"` instead)
    - modifying values in place (add new columns and hide old columns instead)

These commands will probably never be implemented:
  - transpose
  - less common select commands like select-after, select-error

Of course you can still do any of these commands, by first using the VisiData command `freeze-sheet` or `g'` to copy the sheet's values into a new VisiData (i.e. non-vdsql) sheet.

## Bugfixes

- fix key columns on sheets with start=0

# 0.1.1 (2022-08-08)

- limit install of ibis-framework dependencies to sqlite and duckdb

# 0.1 (2022-08-08)

- load data in VisiData for sqlite and duckdb with `vdsql` filetype
- sidebar cycles between SQL, Ibis expression, Substrait, and none
- commands implemented with Ibis expressions
    - frequency table
    - filter rows by single value
    - unfurl-col -> unnest
    - hide column
    - set column type
    - rename col
    - add aggregator (name must be function on Ibis column expr; e.g. use `mean`, `avg` is not available)
    - aggregate immediately
    - sort
    - select-equal
    - stoggle-rows
    - join


