
# Architecture Overview

## The Core Principle: Columns are Functions of Rows

Rows are objects; columns are functions of rows.

Rows can be anything: a tuple of the actual data of the row, some kind of Python object, or even an index into another data structure.

Columns know how to get (and possibly set) their values, given the row.

Therefore rows can be loaded in whatever format is most convenient or efficient, and Columns are extremely lightweight and composable.
This is the key ingredient that gives VisiData its flexibility and power.

### Sheets, Columns, and Cells

Sheets have `rows` (a list of anything) and `columns` (a list of `Column` instances).

All sheets are given a `name`.
Sheet subclasses define their own `columns`, and override the `reload()` method to populate its `rows`.
A simple loader for a new source can be specified in about 20 lines of code.

Each column should also have a `name`, which is shown in its header at the top of the screen, and a `getter`.  Columns may have other properties, such as `setter`, `width`, and `type`.

A cell is the value produced by one column for one row.  Cells are calculated on-demand, so only on-screen cells are computed.

Cell values have a native type (whatever is produced directly by the column function), a coerced type (the type of the column as a whole), a display value (possibly through a format string), a color, and optionally a single-character annotation.

### Commands

Users interact with the displayed sheet via [commands](/design/commands), simple operations which readily compose to perform almost any task.
Each command is bound to one or two (or occasionally three) keystrokes.
Key bindings for basic commands are designed to be intuitive for people who already use terminal-based tools like 'vim'.
Other key bindings are mnemonic and strive to be consistent with other uses of similar bindings.

There are two command prefixes which apply to many commands: `g`, which embiggens the command; and `z`, which smallifies the command.
For instance, the `d` command deletes the current row, whereas `gd` deletes all selected rows, and `zd` sets only the current cell to `None` (effectively deleting its value).
Where there is a reasonable interpretation, prefixes can even be combined: for example, `gzd` applies the `zd` command to all selected rows.

Most keybindings are accessible from any sheet, but some sheets have custom commands which are either only useful in their specific context, or override existing commands.
When overriding commands, these should be consistent with existing usage; for instance, `^C` aborts the most recent asynchronous thread on the current sheet, but `^C` on the Threads Sheet aborts the thread the cursor is on.

A command's [`execstr`](/design/commands/#Python) is also just Python, `exec()`d in the context of the sheet.

### Commandlog

Commands are logged to the [commandlog](/design/commandlog), which may be saved and replayed.
Commandlog replay can be used to restore a previously setup workspace, to run the same set of commands on similar datasets, and to run [automated tests](/test).

### Options

There are a variety of [options](/design/options), which can be set via the Options Sheet, on the command-line, or in the user's `.visidatarc`.

### 
There are two status lines on the bottom row, one on the left and one on the right.
The left status is used for the sheetname and status messages from the last command, and the right status line contains mostly status indicators, like number of rows, the last command, and a progress indicator for asynchronous threads.

### Row selection

[Rows can be selected](/design/selected), individually or in bulk; `g` commands generally operate on selected rows (or, when reasonable, on all rows if no rows are selected).

### Line editor

A custom line editor is included, with [readline command control keys](/design/editor#controls), history (with `UP`/`DOWN`), completion function (with `TAB`/`Shift-TAB`), and ability to launch the user's external `$EDITOR` with `^O` ("open").

### async computation

Functions decorated with [`@asyncthread`](/design/async) will run in a separate thread; this keeps the main user interface responsive (primarily during row loading).

---

These are the main components of the VisiData architecture.
