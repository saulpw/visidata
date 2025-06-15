---
sheet: Sheet
---
# Create a window over consecutive rows

Window functions enable computations that relate the current window to surrounding rows, like cumulative sum, rolling averages or lead/lag computations.

{help.commands.addcol-window}

With large window sizes, [:code]g'[/] (`freeze-sheet`) to calculate all cells and copy the entire sheet into a new source sheet, which will conserve CPU.

## Examples

   date        color  price
   ----------  -----  -----
   2024-09-01  R      30
   2024-09-02  B      28
   2024-09-03  R      100
   2024-09-03  B      33
   2024-09-03  B      99


1. [:keys]#[/] (`type-int`) on the **price** column to type as int.
2. [:keys]w[/] (`addcol-window`) on the **price** column, followed by `1 2`, to create a window consisting of 4 rows: 1 row before the current row, and 2 rows after.
3. To create a moving average of the values in the window, add a new column with a python expression: [:keys]=[/] (`addcol-expr`)
followed by `sum(price_window)/len(price_window)`

date            color   price   price_window            sum(price_window)/len(price_window)
----------      -----   -----   -------------------     -----------------------------------
2024-09-01      R       38      [4] ; 38; 28; 100       41.5
2024-09-02      B       28      [4] 38; 28; 100; 33     49.75
2024-09-03      R       100     [4] 28; 100; 33; 99     65.0
2024-09-03      B       33      [4] 100; 33; 99;        58.0
2024-09-03      B       99      [4] 33; 99; ;           33.0


## Workflows

### Create a cumulative sum 

1. Set the before window size to the total number of rows in the table, and the after rows to 0. In the above example that would be `w 5 0` (`addcol-window`).
2. Add an expression ([:keys]=[/] (`addcol-expr`) of `sum(window)` where `window` is the name of the window function column.

### Compute the change between rows

1. `w 1 0` on the `foo` column to create a window function of size 1 before and 0 after.
2. Add a python expression. The window function column is 'foo_window':
    `=foo_window[1] - foo_window[0] if len(foo_window) > 1 else None`

