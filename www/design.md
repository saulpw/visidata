# The Design of VisiData

1. [Architecture Overview](/design)
2. [Design Goals](/design/goals)
3. [Display Engine](/design/display)
4. [Commands](/design/commands)
5. [Eval context](/design/python)

## Architecture Overview

## Structure, License
vdtui, visidata, bin/vd
   - vdtui is actually what is described in this document.  In a few places, a visidata feature is explained and called out as such.
GPL2 but other apps can use vdtui with MIT
commands are one liners, so you can grep 'Command('

I had to convert my last project to Python3 finally because unicod, and so VisiData was Python3 from the start.  No higher than whatever version comes with the latest Ubuntu LTS (Python 3.4 for VisiData v1.0)

OSS devops notes:
    PyPi is a reasonable distribution platform for Linux and OS X.
    There should be deb and brew packages also, however.
    version % pre 1.0, but semantic versioning post 1.0.

## Sheets

Sheets have Rows (objects) and Columns (functions).

All sheets have a `name` and a list of `sources`.
Sheet subclasses define their own `columns`, and override `reload()` behavior to populate `rows` from their `sources`.

Each column should have a name, which is shown in the header at the top of the sheet.

A cell is the value produced by one column for one row.  Cells are calculated on-demand, so only on-screen cells are computed.

Cell values have a native type (whatever is produced directly by the column function), a coerced type (set on the column as a whole), a display value (possibly through a format string), a color, and an annotation.


Users interact with the displayed sheet via `commands`, small units of functionality which are readily composable to perform most tasks.  Each command is bound to one or two (occasionally three) keystrokes.  Key bindings for basic commands are designed to be intuitive for people who already use command-line tools like 'vim'.  Key bindings for more advanced commands are mnemonic.

To aid with mnemonicism, there are two command prefixes which apply to many commands: `g`, which embiggens the command; and `z`, which smallifies the command.  For instance, the `d` command deletes the current row, but `gd` deletes all selected rows, and `zd` sets the current cell to `None` (effectively deleting it).  Where there is a reasonable interpretation, prefixes can even be combined: for example, `gzd` applies the `zd` command to all selected rows.

Most keybindings are global (accessible from any sheet), but some sheets have custom keybindings which are either only useful in their specific context, or supplant existing commands.  When overriding commands, these should be consistent with existing usage; for instance, `^C` aborts the most recent asynchronous task on the current sheet, but `^C` on the Tasks Sheet aborts the task the cursor is on.

There are a variety of options, settable from within the program itself (via the Options Sheet), the command-line, or in the user's `.visidatarc`.  Users may create or redefine their own global commands in their `.visidatarc` as well. 

This config file is straightforward Python; the syntax for command `execstr` is also just Python, `exec()`ed in the context of the sheet.

There are two status lines on the bottom row, one on the left and one on the right.  The left status is used for sheetname and ephemeral status messages, and the right status line contains mostly status indicators, like number of rows, last keystrokes/command, task progress.

Rows can be selected, individually or *en masse*; 'g' commands generally operate on selected rows (or, where reasonable, on all rows if no rows are selected).

A line editor is included, using [readline commands](), history (with UP/DOWN), completion function (with TAB/Shift-TAB), and ability to launch the user's external `$EDITOR` (with `^Z`).

Functions tagged as `@async` will run in a separate thread; this keeps the main user interface responsive (primarily during row loading).

These are the main components of the VisiData architecture.  Everything else is just details.
