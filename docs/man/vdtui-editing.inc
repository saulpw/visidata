.Sh Editing
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " e"
edits contents of current cell
.It Ic ge
edits contents of current column for selected rows
.It Ic " zd   Delete"
sets contents of current cell to None
.It Ic "gzd  gDelete"
sets contents of cells in current column to None for selected rows
.
.El
.
.Sh "  Commands While Editing Input"
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It Ic "ENTER  ^C"
accepts/aborts input
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
