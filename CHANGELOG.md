# vdsql version history

# 0.1 (2022-08-XX)

- load data in VisiData from any supported [ibis backend](https://ibis-project.org/docs/3.1.0/backends/) with `-f ibis`
- `v` to cycles the sidebar between the generated query in SQL, Python Ibis expression,
    Substrait, and no sidebar
- commands implemented with Ibis expressions
    - `Shift+F` to open Frequency Table; `Enter` to filter source rows by that value
    - `zM` unfurl-col
    - `-` hide column
    - `~`/`@`/`#`/`$`/`%` to set column types
    - `^` to rename col
    - `+` to aggregate (name must be function on Ibis column expr; e.g. use `mean`, `avg` is not available)
    - `z+` to calculate aggregation immediately
    - `[` and `]` family to sort
    - `,` to select rows
    - `gt` to toggle selection
    - `"` to filter selection
    - `&` to join


