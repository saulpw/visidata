- Update: 2018-01-28
- Version: VisiData 1.0

# Combining datasets

## How to join two datasets

1.  Load the datasets into VisiData.

    a. `vd d1.tsv d2.tsv`

    **or**

    b. Press `o` and enter a filepath for each file.

2. Press `S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Press `gC` to open a **Columns sheet** with all columns from selected sheets.
5. Press `!` on the rows that refrences the indices on which the join will be performed. At least one key column, per sheet, should be set.
6. Press `q` to return to the **Sheets sheet**.
7. Optional: If performing a left outer join, use `J` or `K` to reorder the sheets. The first sheet will be the one for whom all rows will be retained.
8. Type `&` followed by the *jointype* to execute the join

jointype            description
---------           -------------
`inner`             keeps only rows which match keys on all sheets
`left outer`        keeps all rows from first selected sheets
`full`              keeps all rows from all sheets (union)
`diff`              keeps only rows NOT in all sheets

## How to append two datasets

1. Load the datasets into VisiData.
2. Press `S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Type `&` followed by `append` to concatenate the selected datasets.
