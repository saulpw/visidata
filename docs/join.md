- Update: 2018-08-19
- Version: VisiData 1.3.1

# Combining datasets

## How to join two datasets

1.  Load the datasets into VisiData.

    a. `vd d1.tsv d2.tsv`

    **or**

    b. Press `o` and enter a filepath for each file.

2. Press `Shift+S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Press `g Shift+C` to open a **Columns sheet** with all of the columns from selected sheets.
5. Press `g!` on the rows that reference the indices on which the join will be performed. At least one key column, per sheet, should be set.
6. Press `Ctrl+^` or `S` to return to the **Sheets sheet**.
7. Optional: If performing a left outer join, use `Shift+J` or `Shift+K` to reorder the sheets. The first sheet will be the one for whom all rows will be retained.
8. Type `&` followed by the *jointype* to execute the join

jointype            description
---------           -------------
`inner`             keeps only rows which match keys on all sheets
`outer`             keeps all rows from first selected sheet
`full`              keeps all rows from all sheets (union)
`diff`              keeps only rows NOT in all sheets
`extend`            keeps all rows and retain **SheetType** from first selected sheet

## How to append two datasets

1. Load the datasets into VisiData.
2. Press `Shift+S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Type `&` followed by `append` to concatenate the selected datasets.
