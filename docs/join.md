- Update: 2020-10-27
- Version: VisiData 2.0.1

# Combining datasets

## How to join two datasets

1.  Open the datasets in VisiData.

    a. `vd d1.tsv d2.tsv`

    **or**

    b. Press `o` and enter a filepath for each file.
2. Press `S` to open up the **Sheets Sheet**. Through here, you can navigate to every sheet by pressing `Enter` on the row it is referenced in.
3. Navigate to the sheets you want the join, and set their shared columns as key columns with `!`.
4. Press `S` to return to the **Sheets sheet**. Select the sheets you want to merge with `s`.
5. Optional: If performing a left outer join, use `Shift+J` or `Shift+K` to reorder the sheets. The first sheet will be the one for whom all rows will be retained.
6. Type `&` to open the join-chooser, and select your desired jointype with `Enter`.

jointype            description
---------           -------------
`inner`             keeps only rows which match keys on all sheets
`outer`             keeps all rows from first selected sheet
`full`              keeps all rows from all sheets (union)
`diff`              keeps only rows NOT in all sheets
`extend`            keeps all rows and retain **SheetType** from first selected sheet
`merge`             Merges differences from other sheets into first sheet

## How to append two datasets

1. Open the datasets with VisiData.
2. Press `Shift+S` to open the **Sheets sheet**.
3. Use `s` or `t` to select the sheets to merge.
4. Type `&` and press `Enter` on `append` to concatenate the selected datasets.
