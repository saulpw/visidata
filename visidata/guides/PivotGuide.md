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

To create a pivot table, 

1. set the primary column(s) as `key columns`. These values will appear along the left side as row headings.
- {help.commands.key_col}

2. The default aggregation provides a total count of the items in each cell. Create any other aggregation columns before building the pivot table. Each aggregation will add a column for each of the pivot columns, (for example sum Red, mean Red, sum Blue, mean Blue, etc.).  

If custom aggregations have been added, the default 'total count' aggregation will not be computed.
- {help.commands.aggregate_col}

3. Navigate to the column that you want to use as the column headings in your pivot table, and create the pivot table:

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

## Melt

To unpivot, see the **MeltGuide**
