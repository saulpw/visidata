---
eleventyNavigation:
  key: Directory Sheet
  order: 99
---

# Directory Sheet (DirSheet)

Open any directory in VisiData to get a **DirSheet**: a browsable, editable view of the filesystem.

~~~
vd .
vd /path/to/directory
~~~

Within VisiData, use `open-dir-current` to open the current working directory.

## Columns

DirSheet shows these columns by default:

Column      Description
------      -----------
directory   parent directory path
filename    file name (key column)
ext         file extension (`/` for directories)
size        file size in bytes
modtime     last modification time

These columns are available but hidden by default (unhide with `-`):

Column      Description
------      -----------
abspath     absolute file path
owner       file owner (Unix)
group       file group (Unix)
mode        file permissions (octal)
filetype    output of `file --brief` (computed async)

Files are sorted by modification time (newest first) by default.

## Opening files

Keystroke(s)        Command                 Action
------------        -------                 ------
`Enter`             `open-row-file`         open file at cursor as a new sheet
`g Enter`           `open-rows`             open all selected files as new sheets
`z Enter`           `open-row-filetype`     open file at cursor, prompting for filetype
`` ` ``             `open-dir-parent`       open parent directory

VisiData detects the filetype from the file extension and opens the appropriate loader (csv, tsv, json, etc.).  Directories open as nested DirSheets.

## File preview

The `open-preview` command opens the file at the cursor in a split pane.  As you navigate the file list, the preview updates automatically to show the current file.

- Tables (csv, tsv, json, etc.) display as proper table sheets
- Text files display as TextSheet
- Directories display as nested DirSheet
- Preview sheets for visible rows are preloaded in the background

`open-preview` is unbound by default; add a keybinding in `.visidatarc`:

~~~
DirSheet.addCommand('p', 'open-preview', 'sheet.previewFile(cursorRow)')
~~~

Close the preview with `g Shift+Z` (close split).

## External editors

Keystroke(s)        Command                 Action
------------        -------                 ------
`Ctrl+O`            `sysopen-row`           open file in `$EDITOR`
`g Ctrl+O`          `sysopen-rows`          open selected files in `$EDITOR`

## Editing the filesystem

DirSheet uses **deferred mode**: edits are staged and applied all at once with `z Ctrl+S`.

### Renaming and moving files

Edit the **filename** column (`e`) to rename a file.  Edit the **directory** column to move it to a different directory (the destination is created if it doesn't exist).

### Deleting files

Mark rows for deletion with `d`.  Commit with `z Ctrl+S`.

- By default (`options.safety_first`), directory deletion uses `os.rmdir` (fails if not empty).
- With `safety_first` disabled, directory deletion uses `shutil.rmtree`.

### Editing metadata

Edit the **size**, **modtime**, **owner**, **group**, or **mode** columns directly.  Changes are applied on commit.

## Copying files

Keystroke(s)        Command                 Action
------------        -------                 ------
`y`                 `copy-row`              copy file at cursor to a destination directory
`gy`                `copy-selected`         copy selected files to a destination directory

## Shell integration

Keystroke(s)        Command                 Action
------------        -------                 ------
`z;`                `addcol-shell`          add column from shell command, with `$columnName` variables

Shell columns run a command for each row, interpolating `$columnName` references with column values.  Both stdout and stderr are captured as separate columns.

## Options

Option          Default     Description
------          -------     -----------
`dir_depth`     `0`         folder recursion depth (0 = only immediate children)
`dir_hidden`    `False`     whether to show hidden files (dotfiles)

Options must be set before loading; reload the sheet after changing them.

## FileListSheet

Opening a `.fdir` file creates a **FileListSheet**: a DirSheet populated from a list of file paths (one per line) instead of a directory listing.
