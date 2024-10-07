---
sheettype: Sheet
---
# Melt is just unpivot

Melt collapses the pivoted columns back into "Variable" and "Value" columns, converting from "wide" format into "long" format. After a melt, there is one row for each value in the pivot table.

1. [Optional] remove a column from the output by hiding it: [:keys]-[/]
2. [Optional] set key columns to keep them unmelted: [:keys]![/]

3a. {help.commands.melt}

A regex melt partially melts the pivoted columns. Provide a regular expression to separate the key column from other columns.

3b. {help.commands.melt_regex}

## Examples

Start with a pivot table, created by pivoting a table with columns `R`,`B`, and key column `date`. There are two aggregators `sum` and `mean`:

   date        sum_R  mean_R  sum_B  mean_B
   ----------  -----  ------  -----  ------
   2024-09-01  30     30      0
   2024-09-02  0              28     28
   2024-09-03  100    100     132    66

Press `Shift+M` for a standard melt:

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

Or press `gShift+M` and then type a `regex` of `(\w+)_(\w)` to separate the aggregator from the column. Only the aggregator will be fully melted. The columns `R` and `B` will remain:

   date        Variable  B    R
   ----------  --------  ---  ---
   2024-09-01  sum       0    30
   2024-09-01  mean           30
   2024-09-02  sum       28   0
   2024-09-02  mean      28
   2024-09-03  sum       132  100
   2024-09-03  mean      66   100

