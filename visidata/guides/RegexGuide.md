---
sheet: Sheet
---
# Matching and Transforming Strings with Regex

Some commands for selecting, searching, and transforming data, accept a regular expression as input.

## Select Rows

- {help.commands.select-col-regex}
- {help.commands.select-cols-regex}

- {help.commands.unselect-col-regex}
- {help.commands.unselect-cols-regex}

## Search

- {help.commands.go-col-regex}

- {help.commands.search-col}
- {help.commands.search-cols}

- {help.commands.searchr-col}
- {help.commands.searchr-cols}

- {help.commands.search-next}
- {help.commands.searchr-next}

- {help.commands.search-keys}

## Substitution

- {help.commands.setcol-regex-subst}
- {help.commands.setcol-regex-subst-all}

`Tab` to move between `search` and `replace` inputs.
An empty `replace` removes the matching string.

# Column Creation

- {help.commands.addcol-regex-subst}
- {help.commands.addcol-split}
- {help.commands.addcol-capture}

## Examples

### Split

Sample input sheet **sales**:

    date        price
    ----------  -----
    2024-09-01  30
    2024-09-02  28
    2024-09-03  100

1. [:code]:[/] (`addcol-split`) on **date** column, followed by `-` to split on hyphens.

    date        date_re             price
    ----------  ----------------    -----
    2024-09-01  [3] 2024; 09; 01    30
    2024-09-02  [3] 2024; 09; 02    28
    2024-09-03  [3] 2024; 09; 03    100

Note that the results in the `date_re` column are lists of length 3.

2. [:code]([/] (`expand-col`) to expand a column with lists into multiple columns with the list elements.

    date        date_re[0]  date_re[1]  date_re[2]  price
    ----------  ----------  ----------  ----------  -----
    2024-09-01  2024        09          01          30
    2024-09-02  2024        09          02          28
    2024-09-03  2024        09          03          100

### Substitution

1. On the **date** column, [:code]*[/] (`addcol-regex-subst`) and type `-`, then `Tab` to "replace" and type `,`.  Then `Enter` to replace all `-` with `,`.

    date        date_re     price
    ----------  ----------  -----
    2024-09-01  2024,09,01  30
    2024-09-02  2024,09,02  28
    2024-09-03  2024,09,03  100

### Capture

1. On the **date** column, [:code];[/] (`addcol-capture`) and type `(\d\d\d\d)` to capture and pull out the year.

    date        date_re     price
    ----------  --------    -----
    2024-09-01  [1] 2024    30
    2024-09-02  [1] 2024    28
    2024-09-03  [1] 2024    100

Note that the results in the `date_re` column are lists of length 1.

2. [:code]([/] (`expand-col`) to expand a column with lists into multiple columns with the list elements.

    date        date_re[0]  price
    ----------  ----------  -----
    2024-09-01  2024        30
    2024-09-02  2024        28
    2024-09-03  2024        100

#### Options

- {help.options.regex_maxsplit}
