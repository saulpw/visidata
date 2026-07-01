---
eleventyNavigation:
  key: Navigation
  order: 3
updated: 2020-07-18
version: VisiData 2.0
---


## How to rapidly scroll through a sheet

Command(s)                    Operation
--------------                ---------------
` ← ↑ → ↓ PgUp PgDn Home End` move as expected
` h`  ` j`  ` k`  ` l`        move cursor **one cell** left/down/up/right (like in vim)
`gh`  `gj`  `gk`  `gl`        move **all the way** to the left/bottom/top/right of sheet
` <`  ` >`                    move up/down the current column to the next **value which differs from current cell**
` {`  ` }`                    move up/down the current column to the next **[selected](/docs/rows#subset) row**

---

## How to search within a sheet

Command(s)              Operation
--------------          ---------------
` /`  ` ?` *regex*      search for *regex* matches up/down the **current** column
`g/`  `g?` *regex*      search for *regex* matches up/down over **all visible** columns
` n`  `Shift+N`              move to next/previous match from last search
`z/`  `z?` *expr*       search by Python *expr* up/down (with column names as variables)

By default, search matches are highlighted in the sheet (like vim's `hlsearch`).

Command(s)              Operation
--------------          ---------------
`highlight-col`         highlight a regex in the current column (without moving)
`highlight-sheet`       highlight a regex in all columns (without moving)
`highlight-clear`       clear all highlight patterns

Undo of a search command does not undo the highlighting; use `highlight-clear` to remove all highlights.

**Options**

Option                         Default                 Description
-----                          -----                   -----
`highlight_search`             `True`                  whether to highlight search matches
`color_highlight_search`       `21 blue on 15 white`   color for highlighted search matches

The following example uses [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).

**Question** Has there been a day where we sold more than 95 **Item**s?

1. Set the type of the **Units** column to integer by moving to the **Units** column and pressing `#`.
2. Type `z/` followed by `Units > 95`.

**Question** What is the **longname** for `gk`?

1. Press `z Ctrl+H` to open the **Commands sheet**.
2. Move to the `keystrokes` column and press `/`, followed by `gk`.
3. Press `c` followed by `longname` to move the cursor to the **longname** column.

---

## Input history

When entering a search regex or other input that has been used before, a history palette appears showing previous inputs.

- `Up`/`Down` cycle through previous inputs (like shell history).
- `Down` past the newest entry restores the original typed text.
- Type to fuzzy search through history.
- `PgUp`/`PgDn` to scroll through the history palette.

The history palette uses the same visual style as the command palette, and is enabled when `cmdpalette` is included in `options.disp_help_flags`.

---

## How to move between sheets

The Sheets Sheet is a list of all sheets that have ever been opened (in order of opening).

The Sheets Stack (`z Shift+S`is the list of active sheets (most recently used at top).

###### Jumping to sheets

1. Press `Shift+S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

###### Jumping away from sheets

Command(s)              Operation
--------------          ---------------
`Ctrl+^`                jump to the previous sheet, without closing the current one
`q`                     quit the current sheet (closes it)

**Note**: A quit/closed sheet is grayed out on the Sheets Sheet.
Closed sheets are removed from the active sheets stack, and the next sheet is then shown.  When the active sheets stack is empty, VisiData exits.

---
