---
eleventyNavigation:
    key: Supported Formats
    order: 99
---

| filetype              | format                                         | VisiData_loader | VisiData saver               | version_added | created | creator                                                       | PyPI dependencies    |
| --------------------- | ---------------------------------------------- | --------------- | ---------------------------- | ------------- | ------- | ------------------------------------------------------------- | -------------------- |
| [csv](#csv)           | Comma\-Separated Values                        | 0\.28           | displayed text               | 0\.28         | 1972    |                                                               |                      |
| [json](#json)         | Javascript Object Notation \(JSON\)            | 0\.28           | typed                        | 0\.28         | 2001    | Douglas Crockford                                             |                      |
| [tsv](#tsv)           | Tab\-Separated Values                          | 0\.28           | displayed text               | 0\.28         |         |                                                               |                      |
| xlsx                  | Excel spreadsheets                             | 0\.28           |                              | 0\.28         | 1987    | Microsoft                                                     | openpyxl             |
| zip                   | ZIP archive format                             | 0\.28           |                              | 0\.28         | 1989    | PKWARE                                                        |                      |
| hdf5                  | Hierarchical Data Format                       | 0\.28           |                              | 0\.28         | 199x    | NCSA                                                          | h5py                 |
| [sqlite](#sqlite)     | sqlite                                         | 0\.42           |                              | 0\.42         | 2000    | D\. Richard Hipp                                              |                      |
| xls                   | Excel spreadsheets                             | 0\.42           |                              | 0\.42         | 1987    | Microsoft                                                     | xlrd                 |
| [fixed](#fixed)       | fixed width text                               | 0\.97           |                              | 0\.97         |         |                                                               |                      |
| [postgres](#postgres) | PostgreSQL database                            | 0\.97           |                              | 0\.97         | 1996    |                                                               |                      |
| [imap](#imap)         | Internet Message Access Protocol               | 2\.12           |                              | 2\.12         | 1988    |                                                               |                      |
| [vd](#vd)             | VisiData command log (TSV)                     | 0\.97           | yes                          | 0\.97         | 2017    | VisiData                                                      |                      |
| [mbtiles](#mbtiles)   | MapBox Tileset                                 | 0\.98           |                              | 0\.98         | 2011    | MapBox                                                        | mapbox\-vector\-tile |
| pbf                   | Protocolbuffer Binary Format                   | 0\.98           |                              | 0\.98         | 2011    | OpenStreetMap                                                 |                      |
| [shp](#shp)           | Shapefile geographic data                      | 0\.98           |                              | 0\.98         | 1993    | ESRI                                                          | pyshp                |
| [html](#html)         | HTML tables                                    | 0\.99           | displayed text               | 0\.99         | 1996    | Dave Raggett                                                  | lxml                 |
| md                    | markdown table                                 |                 | displayed text               | 1\.1          | 2008    |                                                               |                      |
| [png](#png)           | Portable Network Graphics \(PNG\) image        | 1\.1            | from png                     | 1\.1          | 1996    | PNG Development Group                                         | pypng                |
| [ttf](#ttf)           | TrueType Font                                  | 1\.1            |                              | 1\.1          | 1991    | Apple                                                         | fonttools            |
| [dot](#pcap)          | Graphviz diagram                               |                 | from pcap                    | 1\.2          | 1991    |                                                               |                      |
| dta                   | Stata                                          | 1\.2            |                              | 1\.2          | 1985    | StataCorp                                                     | pandas               |
| [geojson](#shp)       | Geographic JSON                                | 2\.2            | yes \(from shp and geojson\) |               | 2008    | http://geojson\.org/                                          |                      |
| sas7bdat              | Statistical Analysis System \(SAS\)            | 1\.2            |                              | 1\.2          | 1976    | SAS Institute                                                 | sas7bdat             |
| sav                   | SPSS statistics                                | 1\.2            |                              | 1\.2          | 1968    | SPSS Inc                                                      |                      |
| spss                  | SPSS statistics                                | 1\.2            |                              | 1\.2          | 1968    | SPSS Inc                                                      | savReaderWriter      |
| xpt                   | Statistical Analysis System \(SAS\)            | 1\.2            |                              | 1\.2          | 1976    | SAS Institute                                                 | xport                |
| [jsonl](#json)        | JSON Lines                                     | 1\.3            | typed                        | 1\.3          | 2013    | Ian Ward                                                      |                      |
| [pandas](#pandas)     | all formats supported by pandas library        | 1\.3            |                              | 1\.3          | 2008    | Wes McKinney                                                  | pandas               |
| parquet               | Apache Parquet                                 | 1\.3            | yes                          | 3\.0          | 2013    | Apache Software Foundation                                    | pyarrow or pandas    |
| [pcap](#pcap)         | network packet capture                         | 1\.3            |                              | 1\.3          | 1988    | LBNL                                                          | dpkt dnslib          |
| pyprof                | Python Profile data                            | 1\.3            |                              | 1\.3          |         |                                                               |                      |
| [xml](#xml)           | eXtensible Markup Language \(XML\)             | 1\.3            | from xml                     | 1\.3          | 1998    | W3C                                                           | lxml                 |
| yaml                  | YAML Ain't Markup Language \(YAML\)            | 1\.3            |                              | 1\.3          | 2001    | Clark Evans                                                   | PyYAML               |
| frictionless          | Frictionless Data                              | 2\.0            |                              | 2\.0          |         | OpenKnowledge Institute                                       | datapackage          |
| jira                  | JIRA/Confluence table markup                   |                 | displayed text               | 2\.0          |         | Atlassian                                                     |                      |
| npy                   | NumPy array format                             | 2\.0            | typed                        | 2\.0          |         |                                                               | numpy                |
| tar                   | Unix Tape Archive                              | 2\.0            |                              | 2\.0          |         |                                                               |                      |
| usv                   | Unicode\-Separated Value                       | 2\.0            | displayed text               | 2\.0          | 1993    | Unicode                                                       |                      |
| xlsb                  | Excel binary format                            | 2\.0            |                              | 2\.0          |         | Microsoft                                                     | xlrd                 |
| [vdj](#vd)            | VisiData command log (JSON)                    | 2\.0            | yes                          | 2\.0          | 2020    | VisiData                                                      |                      |
| [mysql](#mysql)       | MySQL                                          | 2\.0            |                              |               | 1995    | MySQL AB                                                      | MySQLdb              |
| pdf                   | Portable Document Format                       | 2\.0            |                              |               | 1993    | Adobe                                                         | pdfminer\.six        |
| vcf                   | Virtual Contact File \(vCard\)                 | 2\.0            |                              |               | 1995    | Versit Consortium                                             |                      |
| rec                   | recutils database file                         | 2\.0            | displayed text               |               | 2010    | Jose E\. Marchesi                                             |                      |
| eml                   | Multipurpose Internet Mail Extensions \(MIME\) | 2\.0            |                              |               | 1996    | Nathaniel Borenstein and Ned Freed                            |                      |
| [vds](#vd)            | VisiData Sheet                                 | 2\.2            | yes                          | 2\.2          | 2021    | VisiData                                                      |                      |
| ods                   | OpenDocument Spreadsheet                       | 2\.7            |                              |               | 2006    | [OASIS](<https://en.wikipedia.org/wiki/OASIS_(organization)>) | odfpy                |
| lsv                   | awk-like key-value line-separated values       | 2\.7            |                              | v2\.7         |         |                                                               |                      |
| arrow                 | Arrow IPC file format                          | 2\.9            |                              |               | 2016    | Apache Software Foundation                                    | pyarrow              |
| arrows                | Arrow IPC streaming format                     | 2\.9            |                              |               | 2016    | Apache Software Foundation                                    | pyarrow              |
| [vdx](#vd)            | VisiData command log (text)                    | 2\.11           | yes                          | 2\.11         | 2022    | VisiData                                                      |                      |
| mailbox               | All formats supported by mailbox               | 3\.0            |                              |               | 1974    |                                                               | mailbox              |
| jrnl                  | CLI journal                                    | 3\.0            | yes                          | 3\.0          | 2012    | Micah Jerome Ellison                                          |                      |
| [reddit](#api)        | Reddit API                                     | 3\.0            |                              |               | 2005    |                                                               | praw                 |
| [matrix](#api)        | Matrix API                                     | 3\.0            |                              |               | 2014    | The Matrix.org Foundation                                     | matrix\_client        |
| [zulip](#api)         | Zulip API                                      | 3\.0            |                              |               | 2012    | Kandra Labs, Inc                                              | zulip                |
| [airtable](#api)      | Airtable API                                   | 3\.0            |                              |               | 2012    |                                                               | pyairtable           |
| orgmode               | Emacs Orgmode format                           | 3\.0            | yes                          | 3\.0          | 2003    | Carsten Dominik                                               |                      |
| s3                    | Amazon S3 paths and objects                    | 3\.0            |                              |               | 2006    | Amazon                                                        | s3fs                 |
| fec                   | Federal Election Commission                    | 3\.0            |                              |               |         | Federal Election Commission                                   | fecfile              |
| f5log                 | Parser for f5 logs                             | 3\.0            |                              |               |         | f5                                                            |                      |
| toml                  | Tom's Obvious Minimal Language                 | 3\.0            |                              |               |         | Tom Preston-Werner                                            | tomllib              |
| conll                 | CoNLL annotation scheme                        | 3\.0            |                              |               |         | Conference on Natural Language Learning                       | pyconll              |
| [grep](#grep)         | grep command-line utility                      | 3\.1            |                              |               | 1973    | AT&T Bell Laboratories                                        |                      |

# Extra notes about formats

[[GUIDE XsvGuide]]

## fixed {#fixed}
- loader-specific options
    - `fixed_rows` (default: 1000) number of rows to detect fixed width columns from
    - `fixed_maxcols` (default: 0) max number of fixed-width columns to create (0 is no max)

## json {#json}
- loader-specific options
    - `json_indent` (default: None) indent to use when saving json
    - `json_sort_keys` (default: False) sort object keys when saving to json
    - `default_colname` (default: '') column name to use for non-dict rows
- Cells containing lists (e.g. `[3]`) or dicts (e.g. `{3}`) can be expanded into new columns with `(` and unexpanded with `)`.
- All expanded subcolumns must be closed (with `)`) to retain the same structure.
- Support for jsonla was added in 3.0.

## xml {#xml}
- `v` show only columns in current row attributes
- `za` add column for xml attributes

## pcap {#pcap}
- loader-specific options
    - `pcap_internet` (default: 'n') (y/s/n) if save_dot includes all internet hosts separately (y), combined (s), or does not include the internet (n)

## postgres {#postgres}
- loader-specific options
    - `postgres_schema` (default: 'public') the desired schema for the Postgres database
- `vd postgres://`*username*`:`*password*`@`*hostname*`:`*port*`/`*database* opens a connection to the given postgres database.

## imap {#imap}
- `vd "imap://user@domain.com:passwordhere@imap-mailserver.com"` opens a connection to the IMAP server
    - e.g.  `vd "imap://someone@hotmail.com:pass123@imap-mail.outlook.com:993"`
    - e.g.  `vd "imap://someone@gmail.com@imap.gmail.com"`
        - note that you don't specify a password for gmail here -- instead, you will be prompted to follow some instructions

### using VisiData as a pager within psql

In psql:

~~~
\pset format csv
\pset pager always
\setenv PSQL_PAGER 'vd -f csv'
\pset pager_min_lines
~~~

## sqlite {#sqlite}
- supports saving for CREATE/INSERT (not wholesale updates)
- `z Ctrl+S` to commit any `add-row`/`edit-cell`/`delete-row`

## mysql {#mysql}
- loader-specific requirements
    - working mysql / mariadb installation or at least the `libmysqlclient-dev` package (ubuntu; name might be different on other platforms)
    - `mysqlclient` python module in path or virtual environment (`pip install mysqlclient`)
- `vd mysql://`*username*`:`*password*`@`*hostname*`:`*port*`/`*database* opens a connection to the given mysql / mariadb database.

## html {#html}
- loader-specific options
    - `html_title` (default: `'<h2>{sheet.name}</h2>'`) table header when saving to html
- load all `<table>`s in a web page as VisiData sheets.


## shp {#shp}
- Can be edited in raw data form. Images can be plotted with `.` (dot).
- **.shp** files can be saved as **geoJSON**.

## mbtiles {#mbtiles}
- Can be edited in raw data form. Images can be plotted with `.` (dot).

## png {#png}
- Can be edited in raw data form. Images can be plotted with `.` (dot).

## ttf {#ttf}
- Can be edited in raw data form. Images can be plotted with `.` (dot).

## pandas {#pandas}

VisiData has an adapter for **pandas**. To load a file format which is supported by **pandas**, pass `-f pandas data.foo`. This will call `pandas.read_foo()`.

For example:

~~~
vd -f pandas data.parquet
~~~

loads a parquet file. When using the **pandas** loader, the `.fileformat` file extension is mandatory.

To load a hierarchy of parquet files located in folder `data/`, run

~~~
vd -f parquet data/
~~~

or rename the directory to `data.parquet` and run

~~~
vd data.parquet -f pandas
~~~

This should similarly work for any format that has a `pandas.read_format()` function.

## [VisiData Internal Formats](../internal_formats) (.vd, .vdj, .vdx, .vds) {#vd}

- .vd/vdj/.vdx are command log formats suitable for VisiData scripts and macros
- .vds is a multisheet save format that includes some sheet and column metadata

## API (reddit, matrix, zulip, airtable) {#api}
- loader-specific requirements
    - require setting authentication information in `~/.visidatarc` or on the CLI
    - launch the loader with `-f loadername` for steps to obtain and configure authentication credentials

## Grep {#grep}
A .grep file is a JSON lines file. It can be in two formats:
1) A simple container with three fields:
    file - a string with the path to the file where the match was found (absolute or relative path)
    line_no - an integer with the line number in the file where the match was found,
    text - a string with the text of the line that matched.
2) ripgrep `grep_printer` format, described here:
https://docs.rs/grep-printer/latest/grep_printer/struct.JSON.html
