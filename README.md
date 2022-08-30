# vdsql: [VisiData](https://visidata.org) for Databases

A VisiData interface for databases

Powered by [Ibis](https://ibis-project.org).

## Features

- query data in VisiData from any supported backend
- output resulting query in SQL, Substrait, or Python

## Requirements

- Python 3.8
- VisiData v2.10
- Ibis 3.1

### Confirmed supported backends

- SQLite
- MySQL
- PostgreSQL
- DuckDB
- ClickHouse
- Google BigQuery

### [Other backends supported by Ibis](https://ibis-project.org/docs/3.1.0/backends/)

These backends are supported by Ibis and should work, but haven't specifically been tested with vdsql.
If you have have problems connecting, please [file an issue](https://github.com/visidata/vdsql/issues/new).

- Apache Impala
- Datafusion
- Dask
- PySpark
- HeavyAI

## Install latest release

This will install both:
  - the usual `vd` with the vdsql plugin available (use `-f vdsql` to use Ibis instead of builtin loaders),
  - the `vdsql` script that acts identically to `vd` but will use Ibis instead of VisiData's builtin loader.

    pip install vdsql

## Install manually as a VisiData plugin (cutting edge development)

    pip install git+https://github.com/visidata/vdsql.git

    echo "import vdsql" >> ~/.visidatarc

## Usage

### Open a database

    vdsql foo.sqlite  # or .sqlite3
    vdsql mysql://...
    vdsql postgres://...
    vdsql foo.duckdb  # or .ddb
    vdsql clickhouse://explorer@play.clickhouse.com:9440/?secure=1
    vdsql bigquery:///bigquery-public-data

    vdsql <file_or_url>

    vd -f ibis <file_or_url>

where `file_or_url` is any connection string supported by `ibis.connect()` or any of the filetypes and options that VisiData itself supports.

### Commands

A decent amount of work has gone into making `vdsql` work just like VisiData.

You can learn about VisiData starting with the [Intro to VisiData Tutorial](https://jsvine.github.io/intro-to-visidata/) and the [VisiData documentation](https://visidata.org/docs).

There are a few differences, however:

- By default vdsql will only get 10000 rows from a database source.  To get a different number, use `z"` to create a new sheet with a different limit.
- Some VisiData commands aren't implemented using the database engine.
The base VisiData commands can only use the 10000 loaded rows, and this may give incorrect and misleading results.
So these not-implemented commands are disabled, but you can still use the base VisiData commands by first freezing the sheet with `g'` which converts it into a plain old non-database VisiData sheet.

Use `"` (dup-sheet) to run a new base query, including added columns, filtering for the current selection, and applying the current sort order.

### Sidebar

`vdsql` uses the VisiData sidebar (new in v2.9) to show the SQL query for the current view.

- To toggle the sidebar on/off, press `v`.
- To cycle through the various sidebar options, press `zv`.
- To open the sidebar as its own sheet, press `gv`.

Use the `open-sidebar` command (no keyboard shortcut; `Space` to execute a command by its longname, or in the menu) to open a new sheet with the contents of the sidebar, to view or save.

In this way you can compose a SQL expression using VisiData commands, open the SQL sidebar, and save the resulting query to a file (or copy it into your system clipboard buffer).

### Credits

- Saul Pwanson
- Phillip Cloud
