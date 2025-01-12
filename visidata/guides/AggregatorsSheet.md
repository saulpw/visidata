---
sheet: AggregatorSheet
---
# Aggregations like sum, mean, and distinct

Aggregators provide summary statistics for grouped rows.

The current aggregators include:

   min           smallest value in the group
   max           largest value in the group
   avg/mean      average value of the group
   mode          most frequently appearing value in group
   median        median value in the group
   q3/q4/q5/q10  add quantile aggregators to group (e.g. q4 adds p25, p50, p75)
   sum           total summation of all numbers in the group
   distinct      number of distinct values in the group
   count         number of values in the group
   keymax        key of the row with the largest value in the group
   list          gathers values in column into a list
   stdev         standard deviation of values

## View a one-off aggregation of a column

- {help.commands.memo-aggregate} 

## Create an aggregator column

Aggregated columns appear in the **Frequency Table** and **Pivot Table** (grouped sheets).  Aggregated values will also appear at the bottom of their columns in the source sheet.

- {help.commands.aggregate-col}

Then aggregate the sheet with one of the grouping commands:

- {help.commands.freq-col}
- {help.commands.pivot}

Aggregators can be viewed and modified on the **Columns Sheet** in the `aggregators` column.

- {help.commands.columns-sheet}

## The Describe Sheet

To get a predefined set of summary statistics for every column in the sheet, use the **Describe Sheet* :

- {help.commands.describe-all}

## Examples

Sample input sheet **sales**:

   date        color  price
   ----------  -----  -----
   2024-09-01  R      30
   2024-09-02  B      28
   2024-09-03  R      100
   2024-09-03  B      33
   2024-09-03  B      99

1. Move to the `price` column
2. Set it to currency: [:keys]$[/key]
3. Quickly show average price
    - [:keys]z+[/] (`memo-aggregate`) then enter 'avg'
4. Add an `sum` aggregator column:
    - Press [:keys]+[/] (`aggregate-column`) then enter 'sum'
5. Move to the date column [:keys]gh[/]
6. Generate a **Frequency Table** by `date`
    - [:keys]Shift-F[/] (`freq`)


   date        count  price_sum
   ----------  -----  ---------
   2024-09-03  3      232.00
   2024-09-01  1      30.00
   2024-09-02  1      28.00

## Creating new aggregator functions

To add a new aggregator to compute the range of the grouped values (max - min), add the following to `.visidatarc`:

[:code]vd.aggregator('range', lambda values: max(values) - min(values), 'range of values')[/]

The `values` parameter is a list of typed values from the column, with the function returning the aggregated value.
The new aggregator will now be available the next time VisiData is started.
