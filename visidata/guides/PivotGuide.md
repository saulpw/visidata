---
sheet: PivotSheet
---
# Pivot Tables are just Frequency Tables with more columns

Pivot Tables group rows by key columns, summarizing aggregated columns for each distinct value in the current column.

See the **MeltGuide** to unpivot.

## Create a Pivot Table

1. Set the primary column(s) as *key columns*. The values in this column will appear along the left side as row headings, and will be the values the dataset is grouped by.

- {help.commands.key_col}

2. (OPTIONAL) The default aggregation method for pivot cells is `count`. Add other aggregations to columns before building the pivot table. Each aggregation adds a column for every pivot column. See **Examples** below.

Note: Custom aggregations replace the default `count` aggregation.

- {help.commands.aggregate_col}

3. Move the cursor to the column containing the pivot values to be aggregated for each group.

4. Create the pivot table:

- {help.commands.pivot}

## Pivot Sheet

Each cell in the pivot table, as in a **Frequency Table**, links to the underlying rows. Dive into a row to open a new sheet containing the linked rows.

- {help.commands.open-row}

## Examples

Sample input sheet **sales**:

   date        color  price
   ----------  -----  -----
   2024-09-01  R      30
   2024-09-02  B      28
   2024-09-03  R      100
   2024-09-03  B      33
   2024-09-03  B      99


1. [:keys]![/] (`key-col`) on the **date** column to set it as a key column.
2. [:keys]Shift+W[/] (`pivot`) on the **color** column to open a **Pivot Table** grouped by **date**, and summarizing **color**.

   date        R  B
   ----------  -  -
   2024-09-01  1  0
   2024-09-02  0  1
   2024-09-03  1  2

Note that each cell contains the row count because of the default `count` aggregation.

3. [:keys]q[/] (`quit-sheet`) to return to the original **sales** sheet.
4. [:keys]#[/] (`type-float`) on the **price** column to set its type to float.
5. [:keys]+[/] (`aggregate-col`) to add a `sum` aggregate to the **price** column.
6. [:keys]+[/] (`aggregate-col`) to add an `avg` aggregate to the **price** column.
7. [:keys]Shift+W[/] (`pivot`) on the **color** column to create the **PivotSheet**.

This generates each aggregation for all of the pivot columns. As mentioned above, any custom aggregations replace the default `count` aggregation:


   date        sum_R   avg_R   sum_B   avg_B
   ----------  ------  ------  ------  -----
   2024-09-01   30.00   30.00    0.00
   2024-09-02    0.00           28.00  28.00
   2024-09-03  100.00  100.00  132.00  66.00
