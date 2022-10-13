# vdsql: [VisiData](https://visidata.org) for Databases

A VisiData interface for databases

Powered by [Ibis](https://ibis-project.org).

## Features

- query data in VisiData from any supported backend
- output resulting query in SQL, Substrait, or Python

## Requirements

- Python 3.8
- VisiData 2.10.2
- Ibis 3.2

### Confirmed supported backends

- SQLite
- MySQL
- PostgreSQL
- DuckDB
- ClickHouse
- Google BigQuery
- Snowflake

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

## Or install manually as a VisiData plugin (cutting edge development)

    pip install git+https://github.com/visidata/vdsql.git

### Install Ibis backends

To minimize dependencies, only the sqlite backend is included by default.
[Install other backends for Ibis](https://ibis-project.org/docs/3.1.0/backends/#direct-execution-backends) directly, and they will be supported automatically:

    pip install 'ibis-framework[postgres]'

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

- Use `"` (dup-sheet) to run a new base query, including added columns, filtering for the current selection, and applying the current sort order.
- By default vdsql will only get 10000 rows from a database source.  To get a different number, use `z"` to create a new sheet with a different limit.
- Some VisiData commands aren't implemented using the database engine.

The base VisiData commands can only use the 10000 loaded rows, and this might be misleading, so most not-implemented commands should be disabled.

But if you want to use the commands anyway, knowing the dataset is incomplete, you can use `g'` to freeze the current set of loaded rows into a new sheet.

This sheet is a plain (non-database) VisiData sheet, so all VisiData commands can be used on it.

### Freezing the column type

Use `'` to cast the current column to its given type, which persists into future queries (with `"`).

### Sidebar

`vdsql` uses the VisiData sidebar (introduced in v2.9) to show the SQL query for the current view.

- To toggle the sidebar on/off, press `b`.
- To choose a sidebar option, press `zb`.
- To open the sidebar as its own sheet, press `gb`.

In this way you can compose a SQL expression using VisiData commands, open the SQL sidebar, and save the resulting query to a file (or copy it into your system clipboard buffer).

# License

`vdsql` is licensed under the Apache 2.0 license.

Share and enjoy!
