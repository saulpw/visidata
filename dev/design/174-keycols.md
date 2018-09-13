# Key Columns

- key columns must be visible
- hiding a key column also makes it a non-key column
- with "keycol" is a property on the column instead of maintained as a list of keyCols on the sheet, then when a sheet is copied, the keys will be automatically keys unless explicitly disabled on each key column.
- the set of key columns is maintained by the sheet
- But as a list of Sheet.keyCols, the sub-sheet can .clear() the list.
- on the ColumnsSheet, key "rows" (source columns) should be colored the same as key columns.
