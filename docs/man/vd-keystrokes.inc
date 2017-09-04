.Sh Additional Commands for the Cautious
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic ^C 
aborts a command which is expecting an input
.
.El
.
.
.Sh Additional Cursor Movements
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "zt  zz  zb"
scrolls current row to top/center/bottom of screen

.It Ic "zh  zj  zk  zl"
scrolls one cell left/down/up/right
.It Ic "zH          zL"
moves cursor one page left/right
.It Ic "zs          ze"
scrolls sheet to leftmost/rightmost column

.It Ic c
moves to a column whose name matches a regex search
.It Ic r
moves to a specified row number

.It Ic "H  L"
moves current column left/right
.It Ic "J  K"
moves current row up/down
.El
.
.Sh Additional Column Manipulation
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic ";"
creates new colum from capture groups of given regex (cursor must be on an 'example' row, to know how many columns to create)
.It Ic ":"
creates new columns based on a given regex split (also requires an example row)
.It Ic "*"
transform column by regex

.It Ic "'"
creates a frozen copy of current column
.
.Sh Additional Row Manipulation
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " a"
appends a blank row
.El

.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It Sy Clipboard
.It Ic "gy  gd"
copies/deletes all selected rows and moves them to clipboard
.It Ic " p"
pastes row most recently added to clipboard after current row
.It Ic "gp"
pastes all rows from clipboard after current row
.It Ic "^Z"
undoes most recent delete
.El
.Sh Metasheets
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-S"
opens
.Sy S Ns heet metasheet (for managing and navigating the sheet stack)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX 
.It Ic "&"
joins selected sheets, keeping only rows which match keys on all sheets (inner join)
.It Ic "+"
joins selected sheets, keeping all rows from first sheet (outer join, with the first selected sheet being the 'left')
.It Ic "*"
joins selected sheets, keeping all rows from all sheets (full join)
.It Ic "~"
joins selected sheets, keeping only rows NOT in all sheets (diff join)
.El

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-C"
opens
.Sy C Ns olumns metasheet (for making adjustments to various column parameters)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " &"
joins selected source columns
.It Ic "g!"
toggles selected columns as keys on source sheet
.It Ic "g+"
queries for selection of a statistical aggregator for current column
.It Ic "g_" No (underscore)
adjusts widths of selected columns on source sheet
.It Ic "g-" No (hyphen)
hides selected columns on source sheet
.It Ic "g~ g# g% g$ g@"
Sets type of selected columns to str/int/float/currency/date
.El

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-B"
.No opens clip Ns Sy B Ns oard No metasheet (for viewing the paste buffer)

.It Ic "Shift-D"
opens commandlog sheet (for viewing, and replaying, commands executed during current session)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " ^A"
replays command in current row
.It Ic "g^A"
replays contents of entire commandlog
.El

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "^T"
.No opens tasks sheet (for viewing history of async tasks for current session)
.El
.Sh Derived Sheets
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-P"
pushes duplicate sheet with a random subset of
.Ar N No rows of current sheet
.It Ic "Shift-F"
opens frequency table and histogram sheet for current column
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "w"
for histograms of numeric value, toggles between bins with an even interval width and bins with an even frequency height
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-W"
opens pivot sheet for current column (key column and aggregated column are required before pivoting) 
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Enter
pushes sheet of source rows which comprise current pivot cell
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Shift-M"
pushes melted sheet (reverses a pivot)
.El
.Sh "WIP"
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "^X"
.It Ic "^P"
.It Ic "^S"
.It Ic "aggregators"
.El
