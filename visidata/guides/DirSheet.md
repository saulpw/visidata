---
sheettype: DirSheet
---
# Directory Sheet

The **DirSheet** is a display of files and folders in the *source* directory.

To load a **DirSheet**:

- provide a directory as a source on the CLI (e.g. [:code]vd sample_data/[/])
- {help.commands.open_dir_current} (equivalent to [:code]vd .[/])

Use the **DirSheet** to find and open files:

- {help.commands.open_row_file}
- {help.commands.open_rows}
- {help.commands.open_dir_parent}
- {help.commands.sysopen_row}

Use the **DirSheet** as a file manager:

- {help.commands.copy_row}
- {help.commands.copy_selected}
- [:keys]d[/] ([:longname]delete-row[/]) to delete file from filesystem
- [:keys]e[/] ([:longname]edit-cell[/]) to change file metadata (all of the file metadata, except for *filetype*, is modifiable)

Modifications on the **DirSheet** are deferred - they do not take effect on the filesystem itself until they are confirmed.
- {help.commands.commit_sheet}

## Options of Interest (must reload to take effect)

- pass the flag [:code]-r[/] ([:code]--recursive[/]) on the CLI to display all of the files in all subfolders
- {help.options.dir_depth}
- {help.options.dir_hidden}
