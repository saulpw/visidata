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
scrolls one page back/forward

.It Ic  " /   ?" Ar regex No
.No searches for Ar regex No forward/backward in current column
.It Ic  "g/  g?" Ar regex No
.No searches for Ar regex No forward/backward over all visible columns
.It Ic  " n   N"
moves to next/previous match from last search

.It Ic  " <   >"
moves up/down the current column to the next value
.
.El
