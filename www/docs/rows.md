- Update: 2018-01-22
- Version: VisiData 1.0

# Rows

## How to perform operations on a subset of rows

Many commands can be finetuned to operate on rows which are 'selected'.

###### How to specify the subset of rows which are selected

Command(s)         Operation
-----------------  -------------
 `s`  `t`  `u`     selects/toggles/unselects current row
`gs` `gt` `gu`     selects/toggles/unselects all rows
 `|`  `\` *regex*  selects/unselects rows matching *regex* in current column
`g|` `g\` *regex*  selects/unselects rows matching *regex* in any visible column
 `,`               selects rows matching current cell in current column
`g,`               selects rows matching this row in all visible column

An example usage follows.

---

## How to filter rows

1. Press `s` or `t` on the rows to filter.
2. Press

    a. `gd` to delete the selected rows.

    **or**

    b. `"` to open a duplicate sheet with references to the selected rows.  Edits performed within the duplicate sheet will also propagate to the source sheet.

    **or**

    c. `gz"` to open a duplicate sheet with copies of the selected rows.  Any changes will not affect the source sheet.

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
 `[`  `]`          sorts ascending/descending by current column
`g[` `g]`          sorts ascending/descending by all key columns

###### How to sort a numerical column from highest number to lowest:

1. Type the column being sorted by pressing `#` (int) or `%` (float).
2. Press `[` to sort the column from highest to lowest.

###### How to sort a date column in chronological order:

1. Type the column being sorted by pressing `@` (date).
2. Press `]` to sort the column chronologically.

###### How to sort based on two columns

1. Press `!` on those columns to designate them as key columns.
2. Press `g[` or `g]` to sort.

---
