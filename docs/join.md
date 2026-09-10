---
eleventyNavigation:
  key: Combining datasets
  order: 9
Update: 2020-10-27
Version: VisiData 2.0.1
---

The following example uses the files [join_people.csv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/join_people.csv) and  [join_salary.csv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/join_salary.csv).

## How to join two datasets

1.  Open the datasets in VisiData.

    a. `vd join_people.csv join_salary.csv`

    **or**

    b. Press `o` and enter a filepath for each file.
2. Navigate to each of the sheets and set the `ssn` column to be a key column with `!`.  The key columns will act as join columns. You can have multiple key columns per sheet.
3. Press `S` to open up the **Sheets Sheet** and select the sheets you want to merge with `s` or 't'.
4. Optional: If performing a left outer join, use `Shift+J` or `Shift+K` to reorder the sheets. The first sheet will be the one for whom all rows will be retained.
5. Type `&` to open the join-chooser, and select your desired jointype with `Enter`.

jointype            description
---------           -------------
`inner`             keeps only rows which match keys on all sheets
`outer`             keeps all rows from first selected sheet
`full`              keeps all rows from all sheets (union)
`diff`              keeps only rows NOT in all sheets
`extend`            keeps all rows and retain **SheetType** from first selected sheet
`merge`             Merges differences from other sheets into first sheet
`append`            keeps all rows from all sheets; columns from all sheets
`concat`            keeps all rows from all sheets; columns and type from first sheet

## How to combine rows/columns from two datasets

For this we use either the `append` or `concat` join types.

The `append` type forms the union of all rows from all sheets. For columns which exist in multiple sheets,
all data from these columns is combined into a single column.

The `concat` type forms the intersection of all columns from all sheets, and projects the data from those columns in the the original sheets into rows in the resulting sheet.

Steps:

1. Open the datasets with VisiData.
2. Press `Shift+S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Type `&` and press `Enter` on `append` or `concat` to combine the selected datasets.

## Identifying source rows

The `append` and `concat` join types add a hidden `origin_sheet` column that shows which source sheet each row came from. Unhide all hidden columns with `gv`.
