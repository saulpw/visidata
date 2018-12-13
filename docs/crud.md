- Update: 2018-12-12
- Version: VisiData 1.5.1

# Creating sheets, rows and columns

## How to configure the cursor to move right after a successful edit

1. Press `O` to enter the global options menu.
2. Type `r` followed by `cmd` to move the cursor to the **cmd\_after\_edit** option.
3. Press `Enter` to edit the option, and type `go-right`.  Press `Enter` to save the option.

**or**

1. To have the change [persist](/docs/customize), add the following line to the .visidatarc.

    options.cmd_after_edit='go-right'

---

## How to set up a sheet for data collection

1. Type `A` followed by a *number* to open a new blank sheet with that many columns.
2. Press

    a. `a` to add one blank row.

    **or**

    b. `ga` followed by a *number* to add that many blank rows.

3. [Edit the cells](/docs/edit) in any row to contain the column names.
4. While the cursor is on that row, press `g^` to set the header for each column with the contents of the row.
5. Press `d` to remove that row.

---

## How to add a new blank column

1. Press

    a. `za` to add one blank column.

    **or**

    b. `gza` followed by a *number* to add that many blank columns.

---

## How to fill a column with a range of numbers

1. Optional: Use `s` or `t` to select a subset of rows to fill.
2. Move the cursor to the column.
3. Type `gz=` followed by `range(`*n*`)` to set selected rows in that column to the results of an iterator expression. In this case, the range of numbers from 1 to *n*.

---
