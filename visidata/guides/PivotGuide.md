---
sheet: Sheet
---
# Pivot Tables are just Frequency Tables with more columns

Pivot Tables group data by two or more fields. They display one set of values as column headings, another set as row headings, and compute aggregates like the sum or total count for each cell.

## Create a Pivot Table

1. Set the primary column(s) as `key columns`. These values will appear along the left side as row headings.

- {help.commands.key_col}

2. **OPTIONAL** The default aggregation method for pivot cells is `count`. Create any other aggregation columns ( with [:keys]+[/]) before building the pivot table. Each aggregation adds a column for every pivot column. See **Examples** below.

Note: Custom aggregations replace the default `count` aggregation.

- {help.commands.aggregate_col}

3. Navigate to the column containing the pivot column values. 

4. Create the pivot table:

- {help.commands.pivot}

## Dive into the underlying rows for a cell

Each cell in the pivot table, like in a **Frequency Table**, links to the underlying rows.
Explore them with:

- {help.commands.open-row}

## Sort the rows

- {help.commands.sort_asc}
- {help.commands.sort_desc}

## Swap rows and columns

{help.commands.transpose}

## Melt

To unpivot, see the **MeltGuide**

## Examples

Sample input sheet **sales**:

   date        color  price
   ----------  -----  -----
   2024-09-01  R      30
   2024-09-02  B      28
   2024-09-03  R      100
   2024-09-03  B      33
   2024-09-03  B      99

1. Set **date** as the `key` column ([:keys]![/])
2. Navigate to the **color** column 
3. Pivot on the **color** column ([:keys]Shift+W[/]) 

   date        R  B
   ----------  -  -
   2024-09-01  1  0
   2024-09-02  0  1
   2024-09-03  1  2

Note that each cell contains the row count because of the default `count` aggregation.

4. Return to the original **sales** sheet [:keys]q[/] (`close-sheet`)
5. Navigate to the **price** column
6. Set its format to float [:keys]#[/] (`type-float`)
7. Add a 'sum' aggregation [:keys]+[/] (`aggregate-col`))
8. Add an 'avg' aggregation [:keys]+[/] (`aggregate-col`))
9. Navigate to the **color** column 
10. Pivot on the **color** column [:keys]Shift+W[/] (`pivot-command`) 

This generates each aggregation for all of the pivot columns. As mentioned above, any custom aggregations replace the default `count` aggregation:


   date        sum_R   avg_R   sum_B   avg_B
   ----------  ------  ------  ------  -----
   2024-09-01   30.00   30.00    0.00
   2024-09-02    0.00           28.00  28.00
   2024-09-03  100.00  100.00  132.00  66.00

