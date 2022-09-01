# vdsql version history

# 0.2 (2022-08-31)

- fix support for bigquery (thanks @cpcloud for PR #6)
- add clickhouse support
  - add clickhouse dependency installs
- update support for mysql and postgres
- register duckdb with `.ddb` extension
- register sqlite with `.sqlite3` extension

- disable commands unimplemented in vdsql
- add `addcol-expr` (keybinding `=`)
- `zv` to choose sidebar style
- `v` to toggle instead of cycle
- `gv` to open sidebar contents in new sheet
- add `adcol-cast` (keybinding: `'`) to cast column
- add `exec-sql` command
- implement `split-col` by delimiter
- implement `addcol-subst`
- add `dup-limit` (keybinding `z"`) and `dup-nolimit` (keybinding `gz"`)

- add **Frequency Table** support for derived columns (e.g. **Expression Columns**)
- add `options.sql_always_count` (default: False), which determines whether to always query
  a count of the number of results
- add `ibis_type` to **Columns Sheet**
- add title of current sidebar contents
- add aggregation aliases to ibis
- add histogram percent and histogram columns
  - histogram is gated on `options.disp_histo*`
  - histogram is disabled by default
- on dup and freeze-col, cast columns if type is different
- set `options.clean_names` to `True` for all ibis sheets
- [sidebar] do not error if no column expression
- open `PyobjSheet` if not **Frequency Table**
- [join] add suffix for same-named columns from right side
- do not include index names in subtables

## Bugfixes

- filters working with `z|`
- fixes to
  - types
  - aggregates
  - `unselect-rows`
  - outer/full join
  - bq:// scheme
  - `stoggle-rows`
  - `dup-sheet`
- workaround relational integrity issue
- use correct ibis col for groupby
- `stoggle` when none selected should select all
- scoop null use `isnull()`
- [expand] do not drop original struct

## Performance

- add connection pool for concurrent loads
- performance improvements in querying and query counting

## API

- `ibis_filters` is now `ibis_selection`
- `ibis_future_expr` is now `pendir_expr`


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


