---
sheet: Sheet
---
# Matching And Transforming Strings With Regexes

Visidata has built-in support for using Regular Expressions as input for some commands. This includes many commands that enable you to search and transform your data using these patterns.

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

Press `Tab` to move between `search` and `replace` inputs.
Only including a `search` will remove whatever was matched.

# Column Creation

- {help.commands.addcol-regex-subst}

- {help.commands.addcol-split}

- {help.commands.addcol-capture}

## Examples

Sample input sheet **sales**:

    date        price
    ----------  -----
    2024-09-01  30
    2024-09-02  28
    2024-09-03  100

1. [:keys]:[/] (`addcol-split`) on **date** column, followed by `-` to split on `-` character.

    date        date_re             price
    ----------  ----------------    -----
    2024-09-01  [3] 2024; 09; 01    30
    2024-09-02  [3] 2024; 09; 02    28
    2024-09-03  [3] 2024; 09; 03    100

Note that the resulting `date_re` column is of type **List**.

2. Press [:keys]([/] (`expand-col`) to expand it to multiple individual columns.

    date        date_re[0]  date_re[1]  date_re[2]  price
    ----------  ----------  ----------  ----------  -----
    2024-09-01  2024        09          01          30
    2024-09-02  2024        09          02          28
    2024-09-03  2024        09          03          100

3. On the **date** column, press [:keys]*[/] (`addcol-regex-subst`). Beside search type `-`. Press `Tab` and beside replace type `,` to replace all `-` with `,`.

    date        date_re     price
    ----------  ----------  -----
    2024-09-01  2024,09,01  30
    2024-09-02  2024,09,02  28
    2024-09-03  2024,09,03  100

