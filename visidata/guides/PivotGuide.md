# Pivot Tables are just Frequency Tables with more columns

Pivot Tables group data by two or more fields. They display one set of values as column headings, another set as row headings, and compute aggregates like the sum or total count for each cell.

```
+------------+-------+-------+
| date       | color | price |
+------------+-------+-------+
| 2024-09-01 | Red   | 30    |
| 2024-09-02 | Blue  | 28    |
| 2024-09-02 | Green | 64    |
| 2024-09-03 | Red   | 100   |
| 2024-09-03 | Blue  | 33    |
| 2024-09-03 | Blue  | 99    |
+------------+-------+-------+
```

Pivoting on the `date` and `color` columns produces a pivot table that shows how many items of each color were sold each day. Note that here, only the row count, not the sum of prices, is computed for each cell.

```
+------------+-----+------+-------+
| date       | Red | Blue | Green |
+------------+-----+------+-------+
| 2024-09-01 | 1   | 0    | 0     |
| 2024-09-02 | 0   | 1    | 1     |
| 2024-09-03 | 1   | 2    | 0     |
+------------+-----+------+-------+
```

## Create a Pivot Table

To create a pivot table, first set the primary column(s) as `key columns`. These values will appear along the left side as row headings.
- {help.commands.key_col}

The default aggregation provides a total count of the items in each cell. Set other aggregation columns before creating the pivot table. Each aggregation will add a column for each of the pivot columns, (for example sum Red, mean Red, sum Blue, etc.).  If custom aggregations have been added, the default 'total count' aggregation will not be computed.
- {help.commands.aggregate_cols}

Finally, navigate to the column that you want to use as the column headings in your pivot table, and create the pivot table:

- {help.commands.pivot}

Output would be like below (the color names have been shortened to only the first letter for display purposes) if you set the `date` as the key column, and then used the `color` to complete the pivot.

```
+------------+-------+--------+-------+--------+-------+--------+
| date       | sum_R | mean_R | sum_B | mean_B | sum_G | mean_G |
+------------+-------+--------+-------+--------+-------+--------+
| 2024-09-01 | 30    | 30     | 0     |        | 0     |        |
| 2024-09-02 | 0     |        | 28    | 28     | 64    | 64     |
| 2024-09-03 | 100   | 100    | 132   | 66     | 0     |        |
+------------+-------+--------+-------+--------+-------+--------+
```

See that on 2024-09-03, the total sales for Blue hats was $132.

Sort the data:

- {help.commands.sort_asc}
- {help.commands.sort_desc}


See the underlying rows for a cell:

- {help.commands.open-row}


## Swap rows and columns with the transpose command

- {help.commands.transpose}

## Melt (unpivot) a Pivot Table

Pivot tables can be melted (or unpivoted) into regular row and column data in "long" format. Columns are flattened
into a 'variable' column, and the cell content become the 'value' for each row.

- {help.commands.melt}

Here is the Pivot Table from above after a standard `melt`:

```
+------------+----------+-------+
| date       | Variable | Value |
+------------+----------+-------+
| 2024-09-01 | sum_R    | 30    |
| 2024-09-01 | mean_R   | 30    |
| 2024-09-01 | sum_B    | 0     |
| 2024-09-01 | sum_G    | 0     |
| 2024-09-02 | sum_R    | 0     |
| 2024-09-02 | sum_B    | 28    |
| 2024-09-02 | mean_B   | 28    |
| 2024-09-02 | sum_G    | 64    |
| 2024-09-02 | mean_G   | 64    |
| 2024-09-03 | sum_R    | 100   |
| 2024-09-03 | mean_R   | 100   |
| 2024-09-03 | sum_B    | 132   |
| 2024-09-03 | mean_B   | 66    |
| 2024-09-03 | sum_G    | 0     |
+------------+----------+-------+
```

See how the column names have not been split up: `sum_R` and `mean_R`.

You could split the `Variable` column to create a separate column for the aggregation function (mean or sum) and the color (R,G,B).

- {help.commands.addcol_split} 

## Regex-Melt (unpivot) a Pivot Table

When the normal `melt` command on the pivot table, the `Variable` column in the sheet table contains the entire column name (for example 'mean_R'). The columns have been named with a combination of `aggregate function` _ `color`. 

To separate pivot table columns automatically:

- Go back to the pivot table
- Set the `date` column as the key column [:keys]gShift+H[/] [:keys]![/]
- Run {help.commands.melt_regex}

This produces:

```
+------------+----------+-----+----+-----+
| date       | Variable | B   | G  | R   |
+------------+----------+-----+----+-----+
| 2024-09-01 | sum      | 0   | 0  | 30  |
| 2024-09-01 | mean     |     |    | 30  |
| 2024-09-02 | sum      | 28  | 64 | 0   |
| 2024-09-02 | mean     | 28  | 64 |     |
| 2024-09-03 | sum      | 132 | 0  | 100 |
| 2024-09-03 | mean     | 66  |    | 100 |
+------------+----------+-----+----+-----+
```

