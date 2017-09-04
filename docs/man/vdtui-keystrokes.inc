.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic "F1  z?"
displays commands available on the current sheet
.It Ic ^Q
aborts program immediately
.It Ic ^C
aborts user input or current task
.It Ic " q"
drops current sheet (moves back one level)
.It Ic "gq"
quits all sheets (clean exit)
.
.El
.
.Sh "Cursor Movement"
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic "Arrow PgUp Home"
moves as expected
.It Ic " h   j   k   l"
moves left/down/up/right
.It Ic "gh  gj  gk  gl"
moves all the way to the left/bottom/top/right
.It Ic "^B  ^F"
scrolls one page up/down

.It Ic  " /   ?"
regex searches forward/backward in current column
.It Ic  "g/  g?"
regex searches forward/backward over all columns
.It Ic  " n   N"
moves to next/previous match from last search

.It Ic " <   >"
moves up/down this column to a different value
.
.El
.
.
.Sh Column Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic _ Ns " (underscore)"
adjusts width of current column
.It Ic - Ns " (hyphen)"
hides current column (to unhide, go to
.Sy C Ns olumns sheet and Sy e Ns dit its width)
.It Ic \&! Ns
pins current column to the left as a key column
.It Ic ^
edits name of current column
.It Ic "~  #  %  $  @"
sets type of current column to str/int/float/currency/date

.It Ic " ="
creates a new column from the given Python expression, which is computed for each row, using column names are as variables
.It Ic "g="
sets the value in the current column for selected rows to the result of the given Python expression

.El
.
.
.Sh Row Selection
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic " s   u   Space"
selects/unselects/toggles current row
.It Ic "gs  gu  gSpace"
selects/unselects/toggles all rows
.It Ic " |   \e\ "
selects/unselects rows matching by regex in current column
.It Ic "g|  g\e\"
selects/unselects rows matching by regex in any visible column
.It Ic " \&,"
selects rows matching current cell in current column
.It Ic "g\&,"
selects rows matching in all visible columns
.
.El
.
.
.Sh Row Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic " [   ]"
sorts ascending/descending by current column
.It Ic "g[  g]"
sorts ascending/descending by all key columns
.It Ic " \&""
opens duplicate sheet with only selected rows
.It Ic "g\&""
opens duplicate sheet with all rows
.El
.
.
.
.Sh Editing
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic " e"
edit contents of current cell
.It Ic ge
edits contents of current column for selected rows
.It Ic " Delete"
sets contents of current cell to None
.It Ic "gDelete"
sets contents of cells in current column to None for selected rows
.
.El
.
.Sh "  Commands While Editing Input"
.Bl -tag -width XXXXXXXXXXXXXXXX -compact 
.It Ic ENTER
accepts input
.It Ic ^C
aborts input
.It Ic ^Z
launches external $EDITOR to edit contents
.It Ic ^R
reloads initial value
.It Ic "^A  ^E"
moves to beginning/end of line
.It Ic "^B  ^F"
moves back/forward one character
.It Ic "^H  ^D"
deletes previous/current character
.It Ic ^T
transposes previous and current characters
.It Ic "^U  ^K"
clears from cursor to beginning/end of line
.It Ic "Backspace  Del"
deletes previous/current character
.It Ic ^V
inputs next character pressed as a literal
.It Ic Insert
toggles insert mode
.It Ic "Up  Down"
sets contents to previous/next in history
.It Ic "Tab  Shift-Tab"
autocompletes input (when available)
.
.El
.
.
.Sh Metasheets
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic Shift-S
opens 
.Sy S Ns heets sheet: manage and navigate the sheet stack
.It Ic Shift-C
opens
.Sy C Ns olumns sheet: manage the columns of the current sheet
.It Ic Shift-O
opens
.Sy O Ns ptions sheet: change style and behaviour
.It Ic Shift-V
opens readonly
.Sy V Ns iew of contents of the current cell
.It Ic Ctrl-^
jumps to previous sheet
.It Ic " ^E"
opens traceback for most recent error
.It Ic z^E
opens traceback for error in current cell
.It Ic " ` (backtick)"
opens source of current sheet
.
.El
.
.
.Sh Other commands
.
.Bl -tag -width XXXXXXXXXXXXXXXX -compact
.
.It Ic ^L
refreshes screen
.It Ic ^G
shows cursor position and bounds of current sheet
.It Ic ^V
shows version information
.It Ic ^R
reloads current sheet
.It Ic ^D
toggles debug mode (aborts program on any exception)
.
.El
.
.Sh Glossary
.
.Bl -tag -width XXXXXXXXX -compact
.It Ql abort
exit program immediately
.It Ql drop
drop top (current) sheet
.It Ql go
move cursor
.It Ql jump
change to existing sheet
.It Ql load
reload an existing sheet from in-memory contents
.It Ql move
change layout of visible data
.It Ql open
push a sheet to the top of the sheets list (making it immediately visible)
.It Ql scroll
change set of visible rows
.It Ql show
output to status line
.It Ql this
current [row/column/cell] ('current' is also used)
