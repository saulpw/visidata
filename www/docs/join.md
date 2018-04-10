- Update: 2018-03-17
- Version: VisiData 1.1

# Combining datasets

## How to join two datasets

1.  Load the datasets into VisiData.

    a. `vd d1.tsv d2.tsv`

    **or**

    b. Press `o` and enter a filepath for each file.

2. Press `S` to open the **Sheets sheet**.
3. For each sheet that will be merged:

    a. Move the cursor to the row referencing the desired sheet.
    b. Press `Enter` to jump to the sheet referenced in that current cursor row.
    c. Press `!` on the rows that reference the indices on which the join will be performed. At least one key column, per sheet, should be set.
    d. Press `Ctrl+^` or `S` to return to the **Sheets sheet**.

4. Optional: If performing a left outer join, use `J` or `K` to reorder the sheets. The first sheet will be the one for whom all rows will be retained.
5. Type `&` followed by the *jointype* to execute the join

jointype            description
---------           -------------
`inner`             keeps only rows which match keys on all sheets
`outer`             keeps all rows from first selected sheet
`full`              keeps all rows from all sheets (union)
`diff`              keeps only rows NOT in all sheets

## How to append two datasets

1. Load the datasets into VisiData.
2. Press `S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Type `&` followed by `append` to concatenate the selected datasets.
