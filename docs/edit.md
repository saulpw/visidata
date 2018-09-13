- Update: 2018-08-19
- Version: VisiData 1.3.1

# Editing Contents

## How to edit cells

For a summary of all editing commands, see the [man page](/man#edit).

Command         Operation
--------        ----------
 `e`            edit contents of **current cell**
`ge` *text*     set contents of **current column for selected rows** to *text*

While in editing mode, or anytime VisiData expects input (with e.g. `=`, `;`), typical readline commands become available:

Command             Operation
--------            ----------
`Enter`             accepts input
`^C`  `Esc`           aborts input
`^O`                opens external $EDITOR to edit contents
`^R`                reloads initial value
`^A`  `^E`          moves to beginning/end of line
`Backspace`         deletes previous character
`Up`  `Down`        sets contents to previous/next in history
`Tab` `Shift-Tab`   autocompletes input (when available)

---

## How to rename columns

Command     Operation
--------    ----------
  `^`       edits name of **current** column
 `g^`       sets names of **all unnamed visible** columns to contents of **selected** rows (or **current** row)
 `z^`       sets name of **current** column to contents of **current** cell
`gz^`       sets name of **current** column to combined contents of **current** column for **selected** rows

In most cases, `^` is the preferred command. Examples which demo `^` can be seen in [Columns](/docs/columns#derived) and [Group](/docs/group#frequency).

###### How to set the header in an Excel sheet?

For the standard filetypes (e.g. csv, tsv) the loaders assume that the dataset's first `options.header` rows contain the column names. The Excel loader does not because an Excel file can have multiple sheets with varying number of header rows.

1. Press `s` or `t` to select the rows which represent the header rows.
2. Press `g^` to set the names of the headers to the contents of selected rows.

###### How to rename headers using the Columns sheet

1. Press `C` to open the **Columns sheet**.
2. Within the **name** column, move the cursor to the row which represents the source sheet.
3. Type `e` and then input *the new column name*. Press `Enter`.
4. Press `q` to return to the source sheet and see the renamed column.

---
