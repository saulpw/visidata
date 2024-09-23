# Frequency Tables are how you GROUP BY

## About Frequency Tables

A VisiData frequency table groups data into bins using one or more columns, and creates basic summary aggregates of the data. The default aggregates are as follows. However, if user-defined aggregate columns are present, they will also be included.

- count       - (the count of rows in each group)
- percent     - (the percentage of the total rows in each group)
- histogram   - (a visual representation of the percentage)

Here's a tiny dataset of individual hat purchases. Each purchase is for between 1-4 hats.

```
+------------+-------+-------+-------+-------+
| date       | color | count | price | total |
+------------+-------+-------+-------+-------+
| 2024-09-01 | Red   | 1     | 30    | 30    |
| 2024-09-02 | Blue  | 1     | 28    | 28    |
| 2024-09-02 | Green | 2     | 32    | 64    |
| 2024-09-03 | Red   | 4     | 25    | 100   |
| 2024-09-03 | Blue  | 1     | 33    | 33    |
| 2024-09-03 | Blue  | 3     | 33    | 99    |
+------------+-------+-------+-------+-------+
```

A Frequency Table for the `color` column looks like:

```
+-------+-------+---------+----------------------------------------+
| color | count | percent | histogram                              |
+-------+-------+---------+----------------------------------------+
| Blue  | 3     | 50      | ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ |
| Red   | 2     | 33.33   | ■■■■■■■■■■■■■■■■■■■■■■■■■              |
| Green | 1     | 16.67   | ■■■■■■■■■■■■                           |
+-------+-------+---------+----------------------------------------+
```

Given data like this, use a frequency table to answer questions like:

- How many purchases (rows) per day?
- What unique colors were sold?
- How many purchases (rows) per day and color?
- What color generated the most in total sales?
- What is the first purchase (row) for each day?

## Group by a single column

To group by date, navigate to the `date` column and press {help.commands.freq_col}

Note that in addition to getting the counts, the frequency table also provides a list of unique items in the selected column.

For example, navigating to the `color` column and pressing [:keys]Shift+F[/] is a quick way to see the unique colors.

## Group by multiple columns

To group by multiple columns, the grouping columns must be set as key columns.

- use {help.commands.key_col}

In this example, date and color could be set as key columns.

After setting one or more key columns, group by the key columns to create a frequency table:

- {help.commands.freq_keys}

This table can answer how many invoices were created per date and color.

## User-defined aggregates

Note that in the examples above, only the row count was aggregated. Frequently, you want to add additional aggregations (like min, max, sum and/or average). These aggregations must be added before generating the frequency table, and they will show up next to built-in aggregations.

In this example, you can add a `sum` aggregation to the `total` column, and then group by the `color` column:

- Navigate to the `total` column: [:keys]gShift+L[/]
- Add a `sum` aggregate [:keys]+[/] then enter [:keys]sum[/]
- Navigate to the `color` column
- Create the frequency table by pressing [:keys]Shift+F[/]

## Quick Summary

To quickly compare the frequency and aggregates of selected rows compared to the total dataset, use

- {help.commands.freq_summary} 

## Exploring the data

From the `FrequencySheet`, you can explore the underlying data for a single group using the following commands:

- {help.commands.open_row}

To explore multiple rows within the frequency table, select multiple rows, for example with [:keys]t[/] (stoggle-row)

- {help.commands.dive_selected}

In addition to seeing all of the individual rows, sometimes it is helpful to just see the first item from each group. Perhaps you want to see when something first occurred, or to see a representative sample of each group.

- {help.commands.select_first}

The rows are selected in the original sheet, so you must leave the frequency table and return to to the source sheet. One way is with:
- {help.commands.jump_prev}


## Sorting the data

Like with other sheets, sort Frequency Table data by navigating to the desired column and using the sort keys:

- {help.commands.sort_asc}
- {help.commands.sort_desc}

## Using Split Panes with Frequency Tables

There are a few functions that combine Split Panes (see the `SplitplanesGuide`) and Frequency Tables.

If you have an open split [:keys]Shift+Z[/], and create a Frequency Table, it will automatically open in the other split.

Similarly, if you are in a Frequency Table and open a new split, when you explore the group(s) with [:keys]Enter[/] or [:keys]gEnter[/], the detail view will open in the other pane.

