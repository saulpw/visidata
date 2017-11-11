
# Architecture Overview

## The Core Principle: Columns are Functions of Rows

Rows are objects; columns are functions of rows.

Rows can be anything: a tuple of the actual data of the row, or an index into another data structure, or a Python object.

Columns know how to get (or set) their values, given the row.

Therefore rows can be loaded in whatever format is most convenient or efficient, and Columns are extremely lightweight and composable.
This is the key ingredient that gives VisiData its flexibility and power.

## Sheets

Sheets have `rows` (a list of anything) and `columns` (a list of Column instances).

All sheets are given a `name` and a list of `sources`.
Sheet subclasses define their own `columns`, and override `reload()` behavior to populate `rows` from their `sources`.
Loaders for a new source can be specified in about 20 lines of code.

Each column should have a name, which is shown in the header at the top of the sheet.

A cell is the value produced by one column for one row.  Cells are calculated on-demand, so only on-screen cells are computed.

Cell values have a native type (whatever is produced directly by the column function), a coerced type (set on the column as a whole), a display value (possibly through a format string), a color, and an annotation.

Users interact with the displayed sheet via `commands`, small functions which readily compose to perform almost any task.
Each command is bound to one or two (or occasionally three) keystrokes.
Key bindings for basic commands are designed to be intuitive for people who already use command-line tools like 'vim'.
Key bindings for other commands were designed to be mnemonic and intuitive.

There are two command prefixes which apply to many commands: `g`, which embiggens the command; and `z`, which smallifies the command.
For instance, the `d` command deletes the current row, but `gd` deletes all selected rows, and `zd` sets only the current cell to `None` (but effectively deleting its value).
Where there is a reasonable interpretation, prefixes can even be combined: for example, `gzd` applies the `zd` command to all selected rows.

Most keybindings are global (accessible from any sheet), but some sheets have custom commands which are either only useful in their specific context, or override existing commands.
When overriding commands, these should be consistent with existing usage; for instance, `^C` aborts the most recent asynchronous task on the current sheet, but `^C` on the Tasks Sheet aborts the task the cursor is on.

There are a variety of options, settable from within the program itself (via the Options Sheet), the command-line, or in the user's `.visidatarc`.
Users may create or redefine their own global commands in a `.visidatarc` config file, which is just a Python script that gets executed at startup.

The syntax for the command `execstr` is also just Python, `exec()`ed in the context of the sheet.

There are two status lines on the bottom row, one on the left and one on the right.
The left status is used for sheetname and status messages from the last command, and the right status line contains mostly status indicators, like number of rows, last command, and task progress.

Rows can be selected, individually or *en masse*; 'g' commands generally operate on selected rows (or, where reasonable, on all rows if no rows are selected).

A line editor is included, using [readline commands](), history (with UP/DOWN), completion function (with TAB/Shift-TAB), and ability to launch the user's external `$EDITOR` (with `^Z`).

Functions tagged as `@async` will run in a separate thread; this keeps the main user interface responsive (primarily during row loading).

These are the main components of the VisiData architecture.
