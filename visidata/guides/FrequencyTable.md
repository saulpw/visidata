# Frequency Tables are how you GROUP BY

- Group data into bins using one or more columns.
- Count the number of items in each group.
- Also perform custom aggregations for each group.

- Similar to SQL:

   SELECT column_name, COUNT(*) 
   FROM sheet_name 
   GROUP BY column_name 
   ORDER BY COUNT(*) DESC

## Group by a single column

1. Navigate to the target column
- {help.commands.freq_col}

## Group by multiple columns

1. Set one or more columns as key columns:
- use {help.commands.key_col}

2. group by the key columns to create a frequency table:
- {help.commands.freq_keys}

## Aggregators

Add aggregators to one or or more columns BEFORE creating a frequency table. 
- Aggregators include min, max, sum, distinct count, and list.
- Set an appropriate column type for the aggregator target, for example float:  [:key]%[/]

1. Navigate to a column.
2. Add an aggregator (like min, max, sum, list, and distinct count).
- {help.commands.aggregate-col}

3. Add more aggregators to the same or different columns.
4. Generate the Frequency Table. [:keys]Shift+F[/] or [:keys]gShift+F[/]

## Explore the frequency data

Dive into a group to see the underlying row(s) using the **Frequency Table**:

1. Navigate to the target row.
- {help.commands.open_row}

Dive into multiple groups:

- Select multiple rows, for example with [:keys]t[/] (stoggle-row)
- {help.commands.dive_selected}

Return to the frequency table:
- {help.commands.jump_prev}

Select the first row of each group: 

See the selections in the source sheet. For example, select a sample from each each group:

- (`select-first`) - select first source row in each bin
- {help.commands.jump_prev}

## Find Unique Values

The bins of a frequeny table are the unique items.
- The total unique count appears in the bottom right of the window, for example "14 bins".

Copy the unique item list to a new sheet:

1. Generate a frequency table (one or more columns).
2. Hide unwanted columns. [:keys]-[/] or [:keys]Shift+C[/]
3. Copy unique values to a new sheet
- {help.commands.freeze-sheet}

## Count only selected rows

Create an ad-hoc frequeny table that compares the selected rows in the current columns to all rows:

- add aggregators if needed [:keys]+[/]
- {help.commands.freq_summary} 

## Sort the table

Navigate to the target column and sort:

- {help.commands.sort_asc}
- {help.commands.sort_desc}

## Using Split Panes with Frequency Tables

Open a split [:keys]Shift+Z[/], and create a Frequency Table [:keys]Shift+F[/]. 
- The table will automatically open in the other split.

1. Open a Frequency Table
2. open a new split, when you explore the group(s) with [:keys]Enter[/] or [:keys]gEnter[/], the detail view will open in the other pane.

Also see the `SplitplanesGuide`.

## Table Options

- {help.options.disp_histogram}
- {help.options.disp_histlen}

