- Update: 2018-12-12
- Version: VisiData 1.5.1

# Rows

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

1. Press `s` or `t` on the rows to filter.

2. Press

    a. `gd` to delete the selected rows.  The rows can be pasted elsewhere on any sheet of the same type with `gp`.

    **or**

    b. `"` to open a duplicate sheet which has references to the selected rows.  Edits performed within the duplicate sheet will also propagate to the source sheet.

    **or**

    c. `g"` to open a duplicate sheet which has references to all rows, and keeping the selected rows selected.  The selection can be modified on the parent sheet and the new sheet independently, but any changes will be reflected on both sheets.

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

1. Type `R` followed by the *number* of rows you wish included in your random population sample.

---

## How to move, copy and remove rows

Command(s)         Operation
-----------------  -------------
 `J`  `K`          move cursor row down/up
`gJ` `gK`          move cursor row all the way to the bottom/top of sheet


###### How to cut/copy and paste a single row

1. Press `d`/`y` to delete/yank the row and move it to the clipboard.
2. Move the cursor to the desired location.
3. Press `p`/`P` to paste the row after/before current row.

###### How to cut/copy and paste multiple rows

1. Press `s`/`t` on those rows to select them.
2. Press `gd`/`gy` to cut/yank all selected rows to the clipboard.
3. Move the cursor to the desired location.
3. Press `p`/`P` to paste those rows after/before current row.

---

## How to sort rows

Command(s)         Operation
-----------------  -------------
 `[`  `]`          sorts ascending/descending by **current** column
`g[` `g]`          sorts ascending/descending by **all key** columns

###### How to sort a numerical column from highest number to lowest:

1. Set the type of the column being sorted by pressing `#` (int) or `%` (float).
2. Press `[` to sort the column from highest to lowest.

###### How to sort a date column in chronological order:

1. Set the type of the column being sorted by pressing `@` (date).
2. Press `]` to sort the column chronologically.

###### How to sort based on multiple columns

1. Press `!` on those columns to designate them as key columns.
2. Press `g[` or `g]` to sort.

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
