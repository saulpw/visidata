.Sh "Cursor Movement"
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "Arrow PgUp Home"
moves as expected
.It Ic " h   j   k   l"
moves left/down/up/right
.It Ic "gh  gj  gk  gl"
moves all the way to the left/bottom/top/right
.It Ic "     G  gg"
moves all the way to the bottom/top
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
