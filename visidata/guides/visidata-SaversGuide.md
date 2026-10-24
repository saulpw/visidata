# Saving Data

Edits in VisiData stay in memory until you save them. Saving writes the
current sheet (or sheets) out to a file; it does not change how the
original source is loaded next time, unless you explicitly save back
to the source.

## Save the current sheet

- {help.commands.save_sheet}

VisiData prompts for a filename. The default is the source filename,
or the sheet name with the default save filetype if there is no source
file.

## Save without prompting

- {help.commands.save-sheet-really}

Saves the current sheet to its default filename without asking for a
filename or confirmation.

## Save back to the source

- {help.commands.save-source}

Saves the root sheet back to its original source.

## Save all sheets, or selected sheets

- {help.commands.save-all}

Saves all sheets in the sheet stack. Give a directory (a path ending
in `/`) to save each sheet as an individual file in that directory.

- {help.commands.save-selected}

From the Sheets sheet, saves only the selected sheets, in the same way.

A single file only works for formats that support multiple sheets.
Otherwise, save to a directory.

## Save part of a sheet

- {help.commands.save-col}

Saves only the current column.

- {help.commands.save-col-keys}

Saves the key columns plus the current column.

## Choose the format

The file extension decides the format. If no saver matches the
extension, VisiData falls back to the default save filetype, and asks
before saving in that fallback format.

- {help.options.save_filetype}

Append a compression suffix such as `.gz` to save a compressed file.
Saving to a `.zip` file bundles the sheets into one archive.

## Options that affect saving

- {help.options.save_encoding}
- {help.options.safety_first}

For text formats, see also the saving options in the Xsv guide:
`tsv`/`csv` delimiters, quoting, and line terminators.

VisiData asks before overwriting an existing file, so a mistyped
filename does not silently replace good data.

## Full references

- {help.commands.help_commands_all}
- {help.commands.help_commands}
- {help.commands.open_guide_index}
- [:onclick sysopen-help]manpage[/]
- [:onclick https://visidata.org/docs/]online docs[/]
- [:onclick https://visidata.org/docs/api/guides]guide reference[/]
