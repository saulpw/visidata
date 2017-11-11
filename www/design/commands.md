# Design of VisiData: Commands

Commands, initiated through keystrokes, are what make anything happen.
Commands are strings, `exec()`d in a [specific Python context](#python).
Commands may trigger an `error()` or provide a `status()`.
Commands may be 'global' (available in all contexts) or 'sheet-specific'.


## Command(keystrokes, execstr, helpstr)

Creates a Command object that holds 
If the execstr itself is in the commands mapping, then it is taken as an alias, and resolved recursively.
### globalCommand(keystrokes, execstr, helpstr)

Defines a command that is available in every context.  May be overridden in a user `.visidatarc`, or by the Sheets themselves.

To create an alias for a command


To add sheet-specific commands (which will override any existing globalCommands)

### keystrokes

The exact curses names returned by `__` are used as keystrokes.

Prefixes are prepended to the `keystrokes` string: `gh` `g^S`
If prefixes are combined, they are sorted:  `gz=`  Permutations of prefixes are not allowed.

### execstr

A string that will be exec()ed when the keystroke is pressed.

[With this alias system, it's probably time to start naming the fundamental operations by longer-form names, than by their original binding.  Prefer `lowercase-hyphen` style]

The context is the 'vdtui' globals() namespace, and the local context is the current sheet.

For vdtui apps, their modules need to call vdtui.addGlobals(globals()) for their functions and globals to be exposed to execstrs.

### helpstr

* included as a column in .vd scripts
* 'the current' 


# Mnemonics

Most of the keys should have mnemonics given in their helpstrs.
Some larger perspective:

From vim:
  - hjkl
  - zt/zz/zb
     - 'zt' conflicts the describe sheet, where 'zt' toggles selection of the rows of the underlying cell.
  - gg and G and ^G
  - / and ? and N and n to search
     - even though taking ? away for help is almost a deal-breaker
     - and / is the perfect command prefix
     - I wanted the baseline compatibility for people who just want to search.  Maybe ^F/^G could be used instead.
  - d/y/p/P
  - Ctrl-^ to swap top sheets
  - standard ^L from Unix
  - but not '0' for 'gh'

^S is Save, like back in the olden days.

The 'g' prefix generally means 'embiggen', while the 'z' prefix generally means 'smallify'.

Often the single letter commands refer to the current row, the 'g' form act on selected rows (or all rows if none are selected), and the 'z' form shrinks the context to the current cell.
For instance, 'd' deletes the current row, 'gd' deletes all selected rows, and 'zd' sets the current cell to None.
This also makes the combination of 'gz' prefixes make some intuitive sense: 'gzd' sets cells of all selected rows to None (in the current column only).

  - Perhaps '/' should search the whole sheet, and 'z/' should search this column only?
     as '/' searching only this column seems to fool people.

### Selection

- '|' selects rows by regex; '\' unselects by regex.
   - note that these are on the same key.

- '"' duplicates the current sheet, but only takes selected rows.
   - this is different from 

- ',' 'picks up' rows like the current one (',' only in current cell)

### editing

'e'
'ge'
'='
'g='
'z='
'gz='
'Del'/'zd'
'gDel'/'gzd'

### Column Types

The commands to set column types:

 - '!' toggle key column (bang == important)
 - '~' set type to str (tilde looks like a little string)
 - '@' set type to date ('at' a certain datetime)
 - '#' set type to int (number sign)
 - '%' set type to float (percent sign means more fractional than number sign)
 - '$' set type to currency (dollar sign is USD)
 - '^' set column name (points to the header)

Note that these are all symbols on the top shifted row (on US keyboards).

'-' hides a column (sets width to 0), and '\_' toggles the width between `default_col_width` and max width.  Note that these are on the same key (on US keyboards).

### opening Sheets

The commands to open sheets are largely mnemonic, and use shifted letters:

- O - Options
- C - Columns
- S - Sheets
- F - Frequency Table
- I - descrIbe columns (like pandas describe)
- M - [Melt]() (TODO: describe melting)
- W - pivot   (looks like a pivot)
- R - Random sample
- V - View current cell in text sheet (perhaps will be deprecated in favor of ^Y/z^Y)
- D - commanDlog
- A - Add blank sheet

###  Control commands are internal

Some of these commands could reasonably be Shift-letters (like ^T, ^E, ^X, and ^Y).
But they are not, in part because they are assumed to be used infrequently (and mostly during development), and their Shift-letters might be better suited to a different command/sheet in the future.

- ^E - view last error (g^E view all last errors)
- ^R - Reload
- ^D - save command log (shortcut for Shift-D Ctrl-S)
- ^C - cancel task
- ^K - Kill replay
- ^U - paUse/resUme replay
- ^P - Previous status messages (like nethack)
- ^Q - force quit
- ^T - Tasks sheet (should this be Shift-T?)
- ^X - eval python eXpression; g^X exec python expression (for import)
- ^Y - push object sheet of this row; z^Y push object sheet of this cell value

