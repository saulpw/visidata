# vdsql: [VisiData](https://visidata.org) for Databases

A VisiData interface for databases.

Powered by [Ibis](https://ibis-project.org).

## Features

- query data in VisiData from any supported backend
- compose complex queries using VisiData commands instead of writing SQL
- output resulting query in SQL, Substrait, or Python

## Requirements

- Python 3.10+
- VisiData 3.0+
- Ibis 12.0+

## Installation

### Install from pip

This installs both:
  - the usual `vd` with the vdsql plugin available (use `-f vdsql` to use Ibis instead of builtin loaders),
  - the `vdsql` script that acts identically to `vd` but will use Ibis instead of VisiData's builtin loader.

    pip install vdsql

### Install manually (cutting edge development)

    git clone git@github.com:saulpw/visidata.git
    cd visidata/visidata/apps/vdsql
    pip3 install .

### Install Ibis backends

To minimize dependencies, only the sqlite backend is included by default.
[Install other backends for Ibis](https://ibis-project.org/backends/) directly, and they will be supported automatically:

    pip install 'ibis-framework[postgres]'

## Usage

### Connecting to databases

    vdsql <file_or_url>
    vd -f ibis <file_or_url>

where `file_or_url` is any connection string supported by `ibis.connect()` or any of the filetypes and options that VisiData itself supports.

#### Connection examples

    vdsql foo.sqlite          # or .sqlite3, .db
    vdsql foo.duckdb          # or .ddb
    vdsql mysql://...
    vdsql postgres://...
    vdsql clickhouse://play:clickhouse@play.clickhouse.com/?secure=1
    vdsql bigquery:///bigquery-public-data

### Commands

A decent amount of work has gone into making `vdsql` work just like VisiData.

You can learn about VisiData starting with the [Intro to VisiData Tutorial](https://jsvine.github.io/intro-to-visidata/) and the [VisiData documentation](https://visidata.org/docs).

There are a few differences, however:

- `"` (dup-sheet) runs a new base query, including added columns, filtering for the current selection, and applying the current sort order.
- `z"` creates a new sheet with a different row limit.
- `gz"` removes the row limit entirely (fetch all rows).
- `'` casts the current column to its given type, persisting into future queries (with `"`).
- `g'` freezes the current set of loaded rows into a plain VisiData sheet, where all VisiData commands are available.

Some VisiData commands aren't implemented using the database engine.
The base VisiData commands can only use the loaded rows (500 by default), and this might be misleading, so most not-implemented commands are disabled.
If you want to use them anyway, knowing the dataset is incomplete, use `g'` to freeze the sheet first.

### Sidebar

`vdsql` uses the VisiData sidebar to show the SQL query for the current view.

- `b` to toggle the sidebar on/off
- `zb` to choose a sidebar option (pending SQL, base SQL, etc.)
- `gb` to open the sidebar as its own sheet

In this way you can compose a SQL expression using VisiData commands, open the SQL sidebar, and save the resulting query to a file (or copy it into your system clipboard buffer).

### Options

- `ibis_limit` (default: `500`) - max number of rows to fetch per query
- `postgres_schema` (default: `''`, public only) - which PostgreSQL schemas to show (space-separated list; use `*` for all non-system schemas)
- `sql_always_count` (default: `False`) - include total row count in every query
- `disp_ibis_sidebar` (default: `pending_sql`) - which sidebar property to display

## Supported Backends

### Confirmed

- SQLite
- MySQL
- PostgreSQL
- DuckDB
- ClickHouse
- Google BigQuery
- Snowflake

### Backend-specific notes

#### PostgreSQL

By default, only tables from the `public` schema are shown.

To show tables from specific schemas:

    vdsql --postgres-schema='myschema otherschema' postgres://...

To show tables from all non-system schemas:

    vdsql --postgres-schema='*' postgres://...

Note: quote or escape `*` on the command line to prevent shell glob expansion.

#### MySQL

- Requires `libmysqlclient-dev` (on Debian/Ubuntu)
- If you get a timezone warning: `mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql mysql`

### Other backends supported by Ibis

These backends are supported by Ibis and should work, but haven't specifically been tested with vdsql.
If you have problems connecting, please [file an issue](https://github.com/saulpw/visidata/issues/new).

- Apache Impala
- Datafusion
- Dask
- PySpark
- HeavyAI

# License

`vdsql` is licensed under the Apache 2.0 license.

Share and enjoy!
