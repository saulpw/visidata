# [VisiData](https://visidata.org) plugin for [Apache Arrow](https://arrow.apache.org/) columnar stores

- load and save Arrow formats (using [pyarrow](https://arrow.apache.org/docs/python/index.html))
- query various database backends without loading the entire database (using [Ibis](https://ibis-project.org))

## Install latest released version via pip

    pip install vdarrow

## Install VisiData plugin manually

    pip install git+https://github.com/visidata/vdarrow.git

To ~/.visidatarc:

    import vdarrow

## Usage

### deferred execution with Ibis

    vd -f ibis <file_or_url>

where `file_or_url` is any connection string supported by `ibis.connect()`.

## IbisSheet

Only these commands are implemented to use Ibis expressions; others will use the internal VisiData implementation (and will only use the currently loaded rowset, limited to 10000 rows).

- `Shift+F` frequency table
  - on the Frequency Sheet, `Enter` to select one value
- `-` to hide column
- `zM` unfurl-col
- `~`/`@`/`#`/`$`/`%` to set column types
- `^` to rename col
- `+` to aggregate (name must be function on Ibis column expr; e.g. use `mean`, `avg` is not available)
- `z+` to calculate aggregation immediately
- `[` and `]` family to sort
- `,` to select rows
- `gt` to toggle selection
- `"` to filter selection
- `&` to join

### new commands for IbisSheet

- `v` to cycle the sidebar between the generated SQL, the Ibis expression, the Substrait, and no sidebar

## Notes

- the SQL/sidebar expression shows what would be executed during reload, not necessarily what the current view is.
  - For example, opening a table through Ibis only loads the first 10,000 rows.  Sorting the table adds an `ORDER BY` clause to the SQL, but only sorts those first 10,000 rows within VisiData.  To re-run the query including the new ORDER BY clause, use `Ctrl+R` to reload the sheet.
