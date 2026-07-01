---
eleventyNavigation:
  key: Frequency Table Reference
  order: 99
---

# Frequency Table Reference

A frequency table groups source rows by one or more columns and counts the rows in each group.
A pivot table extends this by breaking each group into sub-groups based on a pivot column.
For tutorials and step-by-step workflows, see [Grouping data and descriptive statistics](/docs/group).

Everything below also applies to PivotSheet (`Shift+W`).

## Binning

### Discrete Binning

By default, each unique formatted value in the grouped column becomes its own bin.
Rows are sorted by count, descending.

### Numeric Binning

Set `options.numeric_binning` to True to bin numeric columns into ranges.

- `options.histogram_bins` controls the number of bins. When set to 0 (default), the bin count is the square root of the row count.
- Bin ranges display as "min - max".
- If all values are identical, a single bin is created.
- If there are more bins than distinct values, each value gets its own bin.

### Errors and Nulls

Null and error values get their own bins.
Error bins display as the stringified error value (e.g. `#ERR`).

## Commands

### On source sheet

- `Shift+F` (`freq-col`): open Frequency Table grouped on current column
- `g Shift+F` (`freq-keys`): open Frequency Table grouped by all key columns
- `z Shift+F` (`freq-summary`): open one-line summary for all rows and selected rows
- `Shift+W` (`pivot`): open Pivot Table: group rows by key columns and summarize current column

### On Frequency Table

- `Enter` (`open-row`): open copy of source sheet with rows in the current bin
- `g Enter` (`dive-selected`): open copy of source sheet with rows from all selected bins
- `z Enter` (`dive-except`): open copy of source sheet excluding rows in the current bin
- `gz Enter` (`dive-except-selected`): open copy of source sheet excluding rows in selected bins

## Selection Propagation

Selecting rows on the frequency table also selects the corresponding source rows.
Unselecting works the same way.
Undoing selection changes on the frequency table will also undo them on the source sheet.

## Columns

- **Key columns** from the grouped-by columns. Numeric binned columns use RangeColumn.
- **count**: number of source rows in the bin.
- **percent**: percentage of total source rows in the bin.
- **histogram**: visual bar chart (present when `disp_histogram` is set). Hidden automatically when aggregation columns are added.
- **Aggregation columns**: one column per aggregator set on source columns (via `+`).

## Options

- `options.disp_histogram` (default: `■`): histogram element character
- `options.histogram_bins` (default: `0`): number of bins for histogram of numeric columns (0 = auto)
- `options.numeric_binning` (default: `False`): bin numeric columns into ranges

## Tips

- `g '` (`freeze-sheet`) to create a plain data sheet snapshot of the frequency table.
- Add aggregators on source columns with `+` before opening the frequency table to see summary statistics per bin.
- Select bins with inconsistent values and use `ge` to unify them; the correction propagates back to the source sheet. See [bulk corrections](/docs/edit#bulk-corrections).

---

# Internals

## Row Type

Each row is a `PivotGroupRow` namedtuple with these components:

0. `discrete_keys`: tuple of formatted values for discrete key columns
1. `numeric_key`: range tuple `(min, max)` for numeric bins, or `(0, 0)` if not binned
2. `sourcerows`: list of source rows in this group
3. `pivotrows`: dict mapping pivot values to lists of source rows

## Architecture

- `FreqTableSheet` inherits from `PivotSheet`.
- `groupRows()` iterates source rows, assigns each to a bin by its formatted key values, and populates `sourcerows` and `pivotrows`.
- `addAggregateCols()` creates aggregation columns from any aggregators set on source columns.
- `nonKeyVisibleCols` determines which columns receive aggregation caching after load.

## Pivot-Specific

- `pivotrows` dict maps pivot values to row lists for each group.
- `Column.aggvalue` stores which pivot value a column represents.

## Key Source Files

- `visidata/freqtbl.py` — FreqTableSheet, HistogramColumn, commands
- `visidata/pivot.py` — PivotSheet, PivotGroupRow, RangeColumn, groupRows, addAggregateCols
- `visidata/aggregators.py` — aggregator definitions
