---
eleventyNavigation:
  key: Rows
  order: 4
Update: 2023-10-12
Version: VisiData 3.0
---


## [How to perform operations on a subset of rows](#subset) {#subset}

Many commands can be finetuned to operate on rows which are 'selected'.

###### How to specify the subset of rows which are selected

Command(s)         Operation
-----------------  -------------
 `s`  `t`  `u`     select/toggle/unselect **current** row
`gs` `gt` `gu`     select/toggle/unselect **all** rows
 `|`  `\` *regex*  select/unselect rows matching *regex* in **current** column
`g|` `g\` *regex*  select/unselect rows matching *regex* in **any visible** column
`z|` `z\` *expr*   select/unselect rows matching Python *expr* in **any visible** column
 `,`               select rows matching current cell in **current** column
`g,`               select rows matching **entire current** row in **all visible** columns

An example usage follows.

---

## How to filter rows

1. Press `s` or `t` on the rows to be filtered.

2. Press

    a. `gd` to delete the selected rows.

    **or**

    b. `"` to open a duplicate sheet which has references to the selected rows.  Edits performed within the duplicate sheet will also propagate to the source sheet.

    **or**

    c. `g"` to open a duplicate sheet which has references to all rows, and keeping the selected rows selected.  The selection can be modified on the parent sheet and the new sheet independently, but any changes will not be reflected on both sheets.

    **or**

    d. `z"` to open a copy of the sheet which has copies of the selected rows.  Any changes will not affect the source sheet.

    **or**

    d. `gz"` to open a copy of the sheet which has copies of all rows.  Any changes will be reflected on the source sheet


The following example uses the file [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).


**Question** On which days have we sold less than 10 Binders?

1. Scroll to the `Units` column. Set the type of the `Units` column by pressing `#` (int).
2. Type `z|` followed by `Item == 'Binder' and Units < 10` to select all of the rows where the `Item` is Binder and the number of `Units` is less than 10.
3. Press `"` to open a duplicate sheet with only those selected rows.

---

## How to filter a random subset of rows

1. Type `Space` `random-rows` followed by the *number* of rows you wish included in your random population sample.

---

## How to select rows where the current column is not null or empty?

'Null' cells, by default, are cells which contain `None`. This can be changed with `options.null_value`. Null cells can be set with `zd` (set current cell to `None`) or `gzd` (set selected rows in current column to `None`). Null cells are distinguished with a yellow ∅' symbol on the right hand corner. They are distinct from empty cells (which are `''` in columns of string type.)

1. Type `|` followed by *.* to select all rows without empty or null cells in the current column.

---

## How to select rows where the current column is null?

There are several different options:

- `z,` matches by **typed value** while `,` matches by **display value**. Move to an empty or `None` cell in the column of interest and press `,` to select all empty and `None` cells in that column. Type `z,` on a `None` cell to select all rows that contain `None` in that column. Type `z.` on an empty cell to select all rows that have an empty cell in that column.
- Open a **DescribeSheet** for the current sheet with `Shift+I`. Move to the **nulls** column, and then move to the row which references the source column of interest. Type `zs` to select all null rows for that column.
- `z|` is a command which allows selection by provided Python expression criteria (using column names as variables). For non-numerical columns `z|` followed by **not ColumnName**, will select all empty cells and `None` cells for that column. For numerical columns it will also select cells with `0`.
- [A typed value of Python None is always a `TypedWrapper`](https://www.visidata.org/docs/api/columns.html#user-defined-types), which allows sorting, etc., on columns with None values. For this reason `z|` *ColumnName is None* will not work, thought `z|` *ColumnName.val is None* will work. This is not a recommended approach, though at the moment, it is available.

---

## How to move, copy and remove rows

Command(s)         Operation
-----------------  -------------
 `J`  `K`          move cursor row down/up
`gJ` `gK`          move cursor row all the way to the bottom/top of sheet


###### How to copy and paste a single row

1. Press `y` to copy the row to the clipboard.
2. Move the cursor to the desired location.
3. Press `p`/`Shift+P` to paste the row after/before current row.

###### How to copy and paste multiple rows

1. Press `s`/`t` on those rows to select them.
2. Press `gy` to copy all selected rows to the clipboard.
3. Move the cursor to the desired location.
3. Press `p`/`Shift+P` to paste those rows after/before current row.

###### Note

 VisiData has a universal paste mechanism: it creates new rows on the target sheet and then fills them with values from the copied rows from the previous sheet.

 This value-filling happens positionally, so if columns are missing or in a different order, the values will be in different columns,

---

## How to sort rows

Command(s)         Operation
-----------------  -------------
 `[`  `]`          sorts ascending/descending by **current** column; replace any existing sort criteria
`g[` `g]`          sorts ascending/descending by **all key** columns; replace any existing sort criteria
`z[` `z]`          sorts ascending/descending by **current** column; add to existing sort criteria
`gz[` `gz]`        sorts ascending/descending by **all key** column; add to existing sort criteria

###### How to sort a numerical column from highest number to lowest:

1. Set the type of the column being sorted by pressing `#` (int) or `%` (float).
2. Press `[` to sort the column from highest to lowest.

###### How to sort a date column in chronological order:

1. Set the type of the column being sorted by pressing `@` (date).
2. Press `]` to sort the column chronologically.

###### How to sort based on multiple columns

1. Press `!` on those columns to designate them as key columns.
2. Press `g[` or `g]` to sort.

**or**

1. Sort the first column with `[` or `]`.
2. Sort the next column with `z[` or `z]` to add sorting to the existing criteria.

###### How to increase row height

Press `v` on any **TableSheet** to toggle multi-line rows. This dynamically lengthens rows so that the full content of the column is visible.

Multi-line rows have some limitations; they can't be paged, for instance.  The full contents of a cell can be viewed or edited in an external program like `emacs` or `less`:

* Press `e` on a cell to enter Editing mode. Then scroll left and right to explore its contents.
* Press `Ctrl+O` while in editing mode, to open the contents of the current cell in an external *$EDITOR*.

**TextSheet-specific options**
**TextSheet**s are used for loading `.txt` files in VisiData. They are also the default loaders used for un-identified sources. They are notable for having a single column which has the name "text".

**TextSheet**s have a bonus option `wrap` which will wrap the text into multiple rows, so that it fits the window width.

* On **TextSheet**, press `Shift+O` to open its **OptionsSheet**. Press `Enter` on the `wrap` option, to set it to *True*. Press `q` to return to your **TextSheet**. Reload it with `Ctrl+R`. Note that **reload** undoes an previous modifications you may have made to the **TextSheet**.
* On the commandline, the option `--wrap` will set the `wrap` option to *True* for all **TextSheet**s in that session.
* In your `~.visidatarc`, `options.wrap = True` will set the `wrap` option to *True* for all **TextSheet**s in every session.

---
