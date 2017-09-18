.
.It Ic " e"
edits contents of current cell
.It Ic ge Ar text
.No sets contents of current column for selected rows to Ar text No
.It Ic " zd   Del"
.No sets contents of current cell to Sy None
.It Ic "gzd  gDel"
.No sets contents of cells in current column to Sy None No for selected rows
.
.El
.
.Sh "  Commands While Editing Input"
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
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
.It Ic Insert
toggles insert mode
.It Ic "Up  Down"
sets contents to previous/next in history
.It Ic "Tab  Shift-Tab"
autocompletes input (when available)
.
.El
