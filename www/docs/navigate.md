- Update: 2018-01-22
- Version: VisiData 1.0

# Navigation

## How to rapidly scroll through a sheet

- To move the cursor by one row/column, use the arrow keys or `h`, `j`, `k` and `l` (like in vim).

- To quickly move through a categorical column, use `<` and `>`. They move the cursor up/down the current column to the subsequent value.

- Use `{`/`}` to move up/down the current column to the next [selected](/docs/rows#subset) row.

---

## How to search within a sheet

- Press `/`/`?` followed by a *regex search pattern* to search for matches up/down the current column.

- Press `g/`/`g?` followed by a *regex search pattern* to search for matches over all visible columns.

- Use `n`/`N` to move to the next/previous match from the most recent search.

---

## How to move between sheets

###### Jumping to sheets

1. Press `S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

###### Jumping away from sheets

- Press `^^` to jump to the previous sheet, without quitting the current one.

- Press `q` to quit the current sheet.

---
