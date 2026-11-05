# Saving Data

## Save the current sheet

- {help.commands.save_sheet}
- {help.commands.save_col}
- {help.commands.save_col_keys}

- Saving writes all rows, and only the visible columns.  To save only the selected rows, first open them with `"` (`dup-selected`).
- Text formats like tsv and csv write each value as its column type formats it, so a float column saves `1.23456` as `1.23`.  The json format writes the typed value.  Set the column's **fmtstr** on the **Columns Sheet** (`Shift+C`) to keep more digits.

## Save several sheets

- {help.commands.save_all}

On the **Sheets Sheet**, opened with `Shift+S` (`sheets-stack`):

- {help.commands.IndexSheet.save_selected}

- Formats like xlsx, json, html, and sqlite hold all the sheets in one file.
- End the path with `/` to save each sheet to its own file in that directory, named after the sheet.  Single-sheet formats like tsv and csv require it.

## Choose the format

- The save prompt has a second field, **as filetype**.  `Shift+Up` moves to it.
- A filetype given there overrides the file extension.  With neither, the format is `options.save_filetype`.
- When neither the filetype nor the extension has a saver, a prompt asks to save as `options.save_filetype` instead.
- Add `.gz`, `.bz2`, `.xz`, or `.zst` to the path to compress the file: `out.csv.gz`.

## Overwrite and read-only

- Saving over an existing file asks for confirmation first, except for `--output`.
- `--readonly` to refuse to overwrite existing files, and to refuse `z Ctrl+S` (`commit-sheet`).  **[RO]** shows in the status bar, and the save prompt does not suggest an existing file.
- `--confirm=y` to accept every confirmation, including overwrite.  `--readonly` overrides it.

## Save from the command line

- `--batch --output=out.csv` to save the top sheet after loading and any `--play` replay, with no interface.
- `--output=-` to write it to stdout.
- `--output-filetype=json` to set the output format, instead of the extension.
- `Ctrl+Q` to quit with the top sheet still on the stack, which saves it to the `--output` path, or to stdout when it is piped.  `q` and `gq` save nothing.

## Options

- {help.options.save_filetype}
- {help.options.save_encoding}
- {help.options.safe_error}
- {help.options.overwrite}
- {help.options.confirm}
- {help.options.quitguard}
