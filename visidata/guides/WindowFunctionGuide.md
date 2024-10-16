# Perform operations on groups of rows

The window function creates a new column where each row contains of rows before and/or after the current row in the source column.

Window functions enable computations that relate the current window to surrounding rows, for example:
- cumulative sum
- rolling averages
- lead/lag computations

## Window functions operation on columns

Create a window for a column. The new column will contain the current row, and also any before or after rows specified when creating the window.

- {help.command.addcol-window}

To conserve memory and speed with large windows, one approach is to:
1. add any expressions that operate on the window expression.
2. Freeze the sheet [:keys]g'[/].

## Examples

After creating a window, use a python expression to operate on it.

For example, given a windown column 'win', to create a moving average of the
values in the window, add a new column with a python expression.

```
=sum(win)/len(win)
```

### Create a cumulative sum 

- set the before window size to >= the total number of rows in the table, and the after rows to 0.
- add an expression of `sum(windows)` where `window` is the name of the window function column.

### Compute rank 

https://github.com/saulpw/visidata/discussions/2280#discussioncomment-8314593

### Compute the change between rows

1. Create a window function of size 1 before and 0 after
2. Add a python expression. Assume the window function column is 'win', and the current (integer) column is named seconds:
    `=win[1] - win[0] if len(win) > 1 else None`


