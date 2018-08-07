# initial design notes [2016-10-24]

a. one sheet per screen; no panes
b. rapidly switch between two sheets out of dozens
c. easily reorder single rows; easily send a row to top or bottom
d. heading in a vi direction where applicable (movement)
e. multi-key/compound commands (zt zz zb)?  not yet

f. sheet selector can combine sheets (mark sheets to consolidate, then Combine)
     - `Enter` replaces sheet selection sheet with the sheet at the current row
g. can append rows on all marked sheets to the first marked sheet, by row/column
h. can append sheets by column, joined on the current primary column sort key on each sheet.  tries by column name if no keys
         - possibly maintains one extra index per sheet, by the primary sort key.
         - need to be able to specify inner/outer/cross/diff (intersect, first, union, difference)
i. progress bar is mandatory.  incremental/asynchronous update would be killer.  [2018: it is]

j. header on top row at all times
k. global prefix `g`, indicating that the next command should be applied globally
     - `g/` searches all columns, not just the current
l. random sample
m. slice/split
n. stats page:  Show basic types and statistics of each column (mean, standard deviation, median, range, #empty)

## links
   - https://cran.r-project.org/web/packages/dplyr/index.html
   - https://github.com/OpenRefine/OpenRefine/wiki/User-Guide
   - [BurntSushi/xsv]

# PLAN [2016-10-25]

ideally works with stock Python3, but willing to negotiate numpy if used for interop with adapters.
Probably no other external modules.

1) basic python3 curses display of .csv input 
   a) with cursor movement, search, and pagination
   b) row/column hiding/reordering
   c) multiple sheets, sheet list with sheet stats to manage (and join for 1e/f)
   d) S.columns metasheet, with column stats;
   e) filter/search by regex in column
   f) 'g'lobal prefix

   g) row append all marked sheets into first marked sheet by column name
   h) column append by row key (join: inner/outer/cross/diff)
   i) mark/hide/delete rows (bulk ops)
   j) new column from expression with r.other_column
   k) aggregation (group by current column)
   l) manually edit cell (log to editlog)
   m) bulk transform (diffs to editlog)

2) inputs
   a) 30GB .csv (background build index and cache on fs): foundation for offline data
   b) bigquery (asynchronous updates): foundation for latency
   c) json (hashes)
   d) sqlalchemy
   e) hdf5

3) transforms
   a) allow numpy/pandas functions for 1h/1i

4) output (save to file: full, marked/visible, screen)
   a) .csv
   b) sql (including sheet queries)
   c) hdf5

5) other sheets/features
   a) F builds frequency table for current column (and also F from 1c)
   b) dir/.zip file list (<enter> loads file)

6) documentation
   a) howto add new input
   b) howto add new commands

# README [2016-10-26]

VisiData (vd) is a curses spreadsheet that can be sourced from .csv, sql, json, hdf5 (and others with Python3 adapter).

These become sheets/tables which can be browsed/joined/filtered/sorted with only a few keystrokes.
Derived columns can be added, and cells can expand into other sheets.
The resulting sheet(s) can be saved to any of the above formats also.

Designed to be able to process 10GB+ data files efficiently, and eventually sourcing from cloud data.

Custom sheets can be written that:
   - preprocess the data
   - colorize rows
   - add actions (global, column, row with cell as parameter)
   - add computed columns

e.g. a simple 'stats' derivative sheet that provides median/mean/stddev/etc for each column

The best of xsv, sc, vim, in a single sub-2000-line Python3 script, and extensible.

Great for immediate exploration of datasets to find out what is relevant and what isn't.
