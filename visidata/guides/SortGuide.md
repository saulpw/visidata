# Sorting

## Column types matter

Sorting uses typed values.
Set column types (with `#` for int, `%` for float, `@` for date, etc.) to sort numerically or chronologically instead of lexicographically.

## Viewing the sort order

Open {help.commands.columns_sheet} and check the **sortorder** column.
Positive values indicate ascending order; negative values indicate descending.
The absolute value is the sort priority (1 = highest).

## Sort by one column

Sort all rows by the current column, replacing any existing sort criteria.

- {help.commands.sort_asc}
- {help.commands.sort_desc}

## Sort by key columns

Sort by all key columns at once, replacing any existing sort criteria.

- {help.commands.sort_keys_asc}
- {help.commands.sort_keys_desc}

## Multi-column sort

Sort by multiple columns in priority order.
First sort by the most important column, then add secondary sort columns.

- {help.commands.sort_asc_add}
- {help.commands.sort_desc_add}
- {help.commands.sort_keys_asc_add}
- {help.commands.sort_keys_desc_add}

## Editing the sort order

Toggle a single column in the sort order: add it, remove it, or flip its direction.
Higher-priority sort columns are unchanged; lower-priority columns are removed.

- {help.commands.sort_asc_change}
- {help.commands.sort_desc_change}
