---
sheettype: Sheet
---
# Melt is just unpivot

Pivot tables can be melted (or unpivoted) into regular row and column data in "long" format. The pivoted columns get flattened into a 'Variable' column, and the cell content become the 'Value' for each row.

See the **PivotGuide** for how to create pivot tables.

See **Examples** below for more details of the transformations

## Melt

Melt collapses the pivoted columns back into "Variable" and "Value" columns, converting from "wide" format into "long" format. After a melt, there is one row
for each value in the pivot table.

- {help.commands.melt}

## Regex-Melt 

A regex melt partially melts the pivoted columns. Using a regular expression,  

- {help.commands.melt_regex}

## Examples

Start with a pivot table, created by pivoting a table with color column (with R and B), and two aggregators `sum` and `mean`

   date        sum_R  mean_R  sum_B  mean_B
   ----------  -----  ------  -----  ------
   2024-09-01  30     30      0
   2024-09-02  0              28     28
   2024-09-03  100    100     132    66

### Standard `melt`:

   date        Variable  Value
   ----------  --------  -----
   2024-09-01  sum_R     30
   2024-09-01  mean_R    30
   2024-09-01  sum_B     0
   2024-09-02  sum_R     0
   2024-09-02  sum_B     28
   2024-09-02  mean_B    28
   2024-09-03  sum_R     100
   2024-09-03  mean_R    100
   2024-09-03  sum_B     132
   2024-09-03  mean_B    66

### Big melt: melt-regex

Use the `melt-regex` of `(\w+)_(\w)` to separate the aggregator from the color. Only the aggregator will be fully melted. The colors will remain as columns:

   date        Variable  B    R
   ----------  --------  ---  ---
   2024-09-01  sum       0    30
   2024-09-01  mean           30
   2024-09-02  sum       28   0
   2024-09-02  mean      28
   2024-09-03  sum       132  100
   2024-09-03  mean      66   100

