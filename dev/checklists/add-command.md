# Command checklist

## Writing the command
1) choose where the command will go (module? visidatarc?);
    - most commands should be in thematically-related files
    - imports, then global/Sheet bindings, then helpers, then Sheets, then Sheet-specific bindings
2) choose the appropriate scope for the command;
    - is the command a `globalCommand` (does not require a specific sheet)
    - is the command a  BaseSheet command (for commands that require a sheet but not a tabular sheet)
    - is the command a `Sheet` command (for commands that require rows/columns)
    - or is sheet-specific (only supposed to exist on a particular sheet)
    - note [the relevant syntax](https://github.com/saulpw/visidata/blob/develop/dev/design/169-settings.md#ii-commandskeybindings)
3) at minimum, each command requires a [longname]() and [execstr](); if a command modifies and is in base VisiData, it also requires an [undo]() 
4) optional: choose a default keybinding (see the [available keystrokes](https://visidata.org/kblayout)).
    - [design schema of keystrokes]() (e.g. why we decide to map a command to Ctrl, Shift, g, z, etc)

## Documenting the command (to be done once the command is shippable)
5) add command to [visidata/commands.tsv](https://raw.githubusercontent.com/saulpw/visidata/develop/visidata/commands.tsv);
    - `sheet`: the SheetType the command is bound to
    - `longname`: the [longname]() for the command
    - if the command is bound to a keystroke
        - `prefix`: the prefix for the command, if it has one
        - `key`: the core key that composes the command
        - `keystrokes`: `prefix` + `key`
    - `jump`: does the command result in a sheet being pushed to the top of the stack?
    - `selection`: does the command reference selected rows or affect the selection of a row?
    - `modifies`: if visidata prompts if a user tries to quit a modified sheet, should this command trigger that prompt?
    - `logged`: should this command be logged in the cmdlog?
    - `video`: is this command covered in the [vd case studies]()
    - `menupath`: the original form of the longnames; when they were used as a pathway through the vd menu
    - `helpstr` a documentation of what the command does; should mirror what is contained in the manpage
    - sort by `longname` with `[` and then sort `sheet` with `]`
6) if the command has been bound to a key, add it to the [man page](https://github.com/saulpw/visidata/blob/develop/visidata/man/vd.inc);
    - render the manpage to ensure that its beauty is intact
7) include command longname and keybinding in commit headline.
    - add to CHANGELOG before release
8) quality check that there are no errors in commands sheet (z^H)

