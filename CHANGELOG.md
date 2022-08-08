# vdsql version history

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


