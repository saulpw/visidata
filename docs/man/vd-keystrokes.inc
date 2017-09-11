.so vdtui-main.inc
.so vdtui-cursor.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " H   L"
moves current column left/right
.It Ic "gH  gL"
moves current column to be the leftmost/rightmost non-key column
.It Ic " J   K"
moves current row up/down
.It Ic "gJ  gK"
moves current row to the top/bottom of sheet

.It Ic c Ar regex
moves to a column whose name matches the given regex
.It Ic r Ar number
moves to the given row number

.It Ic "zt  zz  zb"
scrolls current row to top/center/bottom of screen

.It Ic "zh  zj  zk  zl"
scrolls one cell left/down/up/right
.It Ic "zH          zL"
moves cursor one page left/right
.It Ic "zs          ze"
scrolls sheet to leftmost/rightmost column

.El
.
.so vdtui-column.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "z=" Ar expr
evaluates given Python expression on current row, using column names as variables, and displays result on status line
.It Ic "g^"
sets names of all visible columns to contents of current row

.It Ic " '"
creates a frozen copy of current column
.
.It Ic "g'"
pushes a frozen copy of current sheet

.It Ic "\&;" Ar regex
creates new colum from capture groups of given regex (cursor must be on an 'example' row, to know how many columns to create)
.It Ic "\&:" Ar regex
creates new columns based on a given regex split (also requires an example row)
.It Ic "*" Ar regex Ns Sy / Ns Ar subst No
.No replace Ar regex No with Ar subst Ns , which may include backreferences (\\\1 etc)
.so vdtui-row.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " a"
appends a blank row
.El

.Sh Clipboard
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It Ic "gy  gd"
copies/deletes all selected rows and moves them to clipboard
.It Ic " p"
pastes row most recently added to clipboard after current row
.It Ic "gp"
pastes all rows from clipboard after current row
.It Ic " ^Z"
undoes most recent delete
.It Ic "g^Z"
undoes deletion of all rows which are referenced in the clipboard

.El
.so vdtui-editing.inc

.Sh Sheets Sheet (Shift-S)
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
jumps to sheet referenced in current row
.It Ic "&"
inner join of selected sheets, keeping only rows which match keys on all sheets
.It Ic "+"
outer join of selected sheets, keeping all rows from first selected sheet
.It Ic "*"
full join of selected sheets, keeping all rows from all sheets
.It Ic "~"
joins selected sheets, keeping only rows NOT in all sheets (diff join)
.El
.Sh Options Sheet (Shift-O)
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
edits option
.El
.Sh Columns Sheet (Shift-C)
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " &"
adds column from concatenating selected source columns
.It Ic "g!"
toggles selected columns as keys on source sheet
.It Ic "g+"
queries for selection of a data aggregator for current column
.It Ic "g_" No (underscore)
adjusts widths of selected columns on source sheet
.It Ic "g-" No (hyphen)
hides selected columns on source sheet
.It Ic "g~ g# g% g$ g@"
Sets type of selected columns to str/int/float/currency/date
.El
.Sh Clipboard Sheet (Shift-B)

.Sh Describe Sheet (Shift-I)
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "zs  zu"
selects/unselects rows on source sheet which are being described in current cell
.It Ic "zEnter"
pushes a copy of rows from source sheet which are being described in current cell
.El
.Sh Commandlog Sheet (Shift-D)
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " ^A"
replays command in current row
.It Ic "g^A"
replays contents of entire commandlog
.El
.Sh Frequency Table (Shift-F)
Groups rows by key, including columns for each aggregation of a source column.  Set aggregators on columns with '+' (or by 'e'dit on its 'C'olumns sheet) before pressing Shift-F to use the current column as the key.
.Sy gF No groups by all key columns on the source sheet.
.Bl -tag -width XXXXXXXXXXXXXXX -compact

.It (commands specific to the Frequency Table)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "s  u  Space"
selects/unselects/toggles rows on source sheet which are being described in current cell
.It Ic "w"
for histograms of numeric value, toggles between bins with an even interval width and bins with an even frequency height
.El
.Sh Pivot Sheet (Shift-W)
Set key column(s) and aggregators on column(s) before pressing Shift-W on the column to pivot.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Enter
pushes sheet of source rows which comprise current pivot cell
.El
.Sh Melted Sheet (Shift-M)
Pushes melted sheet (unpivot), with all non-key columns reduced to Variable-Value rows.
.Sh Tasks Sheet (^T)

.Sh Data toolkit
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "o" Ar input
opens 
.Ar input No in Sy VisiData
.It Ic "^S"
saves current sheet to new file
.It Ic "^D"
saves commandlog to new .vd file
.It Ic "Shift-A"
.No pushes new blank sheet with Ar N No columns

.It Ic " +" Ar aggregator
queries for selection of a data aggregator for current column (result is displayed on frequency-table sheet)
.It Ic "z+" Ar aggregator
queries for method of data aggregation for cells of selected rows in current column (result is displayed on status line)
.Ar N No rows of current sheet
.It Ic "Shift-P" Ar N
pushes duplicate sheet with a random subset of 
.Ar N No rows
.so vdtui-other.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "^P"
pushes status history sheet
.It Ic "^X"
evalutes Python expression and pushes sheet for browsing resulting Python object
.It Ic "^A"
pushes sheet for viewing current row as Python object
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
dives further into Python object
.It Ic "\&."
toggles whether methods and hidden properties are shown

.El
