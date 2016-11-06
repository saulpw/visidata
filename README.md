# VisiData

The Swiss Army Knife for Data Exploration

A console spreadsheet tool for discovering and arranging data

- core script is a standalone Python3.x script

- explore .csv, .json, .h5 files
- rows are loaded on demand, so 100GB .csv files can be browsed instantly
- same for remote datasets like bigquery/redshift or via sqlalchemy to RDBMS

- '=' create new column from python eval expression

- select rows by regex or python expression
- sort rows by one or more columns
- inner/outer/cross/diff join rows from multiple sheets by matching key columns
- aggregate rows by key columns, rollup functions (mean/min/max) provided for other columns

- 'Q' pushes a new sheet with the frequency table of the current column
- 'gQ' pushes a new sheet with one row per column of the current sheet, with distinct/min/max/mean/median/stddev of each column

- save sheet as .csv/tsv, .json, or into .h5 table
- save layout for future instances

- custom sheet arrangements in Python3 scripts for repeated use on similar datasets that:
   - preprocess the data
   - coloring rows by matching regex or expression
   - make <enter> 'dive' into cells by pushing a parameterized sheet onto the stack
   - add other actions
   - add computed columns

- all edits and transforms added to changelog

Great for immediate exploration of datasets to find out what is relevant and what isn't.
Usable via remote shell.
Download a 50k standalone script onto a system with Python3 and get cracking.

## Requires
    - Python 3.2
    - h5py (if reading/writing HDF5)

## Keybindings

| Keybinding | Action |
| --- | --- |

|    F1/?   | Show keybindings for this screen |

|   h/j/k/l | (or arrows) move cell cursor left/down/up/right (g to move all way) |
|   H/M/L   | move cursor to top/middle/bottom of screen |
|   J/K     | skip down/up to next value in column |
| pgdn/pgup | scroll sheet one page down/up (minus stickied rows/columns.  g goes to first/last page) |
|   H/J/K/L | (or shift-arrows/pgdn/pgup)  |
|^H/^J/^K/^L| (or ctrl-arrows) move column/row left/down/up/right (changes data ordering) (g to 'throw' it all the way) |
|    .      | mark this column as a 'key' column |

|   <#>G    | go to row <#>.  without number, go to last row |
|    ^G     | show sheet status line |

|    /      | Search by regex |
|           | Search by row expression |
|    n      | Go to next search match |
|    p      | Go to previous search match |

|    s      | save current sheet to new file (g saves all sheets to new .h5 file) |
|    ^R     | reload files (keep position) |

|Prefixes |
|    g      | selects all columns or other global context for the next command only |

|Sheet setup and meta-sheets |
| ctrl-^    | toggle to previous sheet |

|    S      | view current sheet stack (g views list of all sheets) |
|    C      | column chooser |
|    -      | Hide current column |
|    _      | Expand current column to fit all column values on screen |
|    +      | Expand all columns to fit all elements on screen |
|    =      | Add derivative column from expression |

|(shift-letters usually create new pages) |
|    E      | view last full error (e.g. stack trace) |

|    Q      | build frequency table for current column (g builds stats (distinct/min/max/mean/stddev) for all columns) |

|    SPACE  | add current row to selected rows (g selects all rows) |
|    0      | unselect all rows |
|    m      | add regex to mark list |
|           | add eval expression to mark list |
|    *      | select all rows |

|    M      | view select list for this sheet |
|           | mark all visible rows |
|           | mark all rows |
|           | hide marked rows |
|           | only show marked rows |
|           | mark all hidden rows and unhide |

|row filter (WHERE) |
|    Show all items (clear include/exclude lists) |
|    \|     | filter by regex/expression in this column (add to include list) |
|    \\     | ignore by regex/expression in this column (add to exclude list) |
|    ,      | filter the current column by its value in the current row |
|    { }    | Sort primarily by current column (asc/desc) |
|    [ ]    | Toggle current column as additional sort key (asc/desc) |
|    r      | Remove all sort keys (does not change current ordering) |
|    R      | show list of filters/ignore |

|           | skip down to next change in row value |
 
|aggregation (GROUP BY) |
|            group by current column locally (g to make global groups) |
|            ungroup current column (g to ungroup all columns) |
 
|    ^R      reload current sheet from sources |
