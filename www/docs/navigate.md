- Update: 2018-08-19
- Version: VisiData 1.3.1

# Navigation

## How to rapidly scroll through a sheet

Command(s)              Operation
--------------          ---------------
` ← ` `↑`   ` →`   ` ↓` move as expected
` h`  ` j`  ` k`  ` l`  move cursor left/down/up/right (like in vim)
`gh`  `gj`  `gk`  `gl`  move **all the way** to the left/bottom/top/right of sheet
` <`  ` >`              move up/down the **current** column to the next value which differs from **current** cell
` {`  ` }`              move up/down the **current** column to the next [selected](/docs/rows#subset) row.


---

## How to search within a sheet

Command(s)              Operation
--------------          ---------------
` /`  ` ?` *regex*      search for *regex* matches up/down the **current** column
`g/`  `g?` *regex*      search for *regex* matches up/down over **all visible** columns
` n`  ` N`              move to next/previous *regex* match from last search
`z/`  `z?` *expr*       search by Python *expr* up/down in **current** column (with column names as variables)

The following example uses [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).

**Question** Has there been a day where we sold more than 95 **Item**s?

1. Scroll to the **Units** column. Set the type of the **Units** column by pressing `#` (int).
2. Type `z/` followed by `Units > 95`.

**Question** What is the **longname** for `gk`?

1. Press `z^H` to open the **Commands sheet**.
2. Type `z/` followed by `'gk' in keystrokes`.
3. Press `c` followed by `longname` to move the cursor to the **longname** column.

---

## How to move between sheets

###### Jumping to sheets

1. Press `S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

###### Jumping away from sheets

Command(s)              Operation
--------------          ---------------
`Ctrl+^`                jump to the previous sheet, without closing the current one
`q`                     quit the current sheet (closes it)

**Note**: When sheets are 'closed', they will cease to be referenced by the **Sheets sheet**. Press `gS` to access them again through the **Sheets graveyard**.

---
