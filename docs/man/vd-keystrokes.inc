.so vdtui-main.inc
.so vdtui-cursor.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " c" Ar regex
.No moves to the next column with name matching Ar regex No
.It Ic " r" Ar regex
.No moves to the next row with key matching Ar regex No
.It Ic "zc  zr" Ar number
.No moves to the given column/row Ar number No
.Pp
.It Ic " H   J   K   L"
slides current row/column left/down/up/right
.It Ic "gH  gJ  gK  gL"
slides current row/column all the way to the left/bottom/top/right of sheet
.Pp
.It Ic "zt    zz    zb"
scrolls current row to top/center/bottom of screen

.It Ic "zh  zj  zk  zl"
scrolls one left/down/up/right
.It Ic "zH          zL"
moves cursor one page left/right
.It Ic "zs          ze"
scrolls sheet to leftmost/rightmost column

.El
.
.so vdtui-column.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "z=" Ar expr
.No evaluates Python Ar expr No on current row and displays result on status line
.It Ic "g^"
sets names of all visible columns to contents of current row

.It Ic " '"
adds a frozen copy of current column with all cells evaluated
.
.It Ic "g'"
pushes a frozen copy of current sheet with all visible columns evaluated

.It Ic "\&:" Ar regex
.No adds new columns from Ar regex No split; # columns determined by example row at cursor
.It Ic "\&;" Ar regex
.No adds new columns from capture groups of Ar regex Ns ; also requires example row
.It Ic "*" Ar regex Ns Sy / Ns Ar subst No
.No replace Ar regex No with Ar subst Ns , which may include backreferences ( Ns Sy \e1 No etc)
.so vdtui-row.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.El

.Sh Clipboard
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It Ic "Shift-B"
opens clipboard sheet
.It Ic " y  gy"
copies current/all selected row(s) and appends to clipboard sheet
.It Ic " p"
pastes most recent clipboard row after current row
.It Ic "gp"
pastes all clipboard rows after current row
.It Ic " ^Z"
undoes most recent delete in clipboard sheet
.It Ic "g^Z"
undoes deletion of all rows in clipboard sheet

.El
.Sh Editing
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " a"
appends a blank row
.It Ic " d  gd"
deletes current/all selected row(s) and appends to clipboard sheet
.so vdtui-editing.inc

.Sh Data Toolkit
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " o" Ar input
opens
.Ar input No in Sy VisiData
.It Ic "^S" Ar filename
.No saves current sheet to Ar filename No in format determined by extension (default .tsv)
.It Ic "^D" Ar filename.vd
saves commandlog to new .vd file
.It Ic "Shift-A" Ar number No
.No pushes new blank sheet with Ar number No columns

.It Ic " +" Ar aggregator
.No adds Ar aggregator No to the current column (see Sy "Frequency Table" Ns )
.It Ic "z+" Ar aggregator
.No displays result of Ar aggregator No over values in selected rows for the current column
.It Ic "Shift-P" Ar number
pushes duplicate sheet with a random population subset of
.Ar number No rows
.so vdtui-other.inc

.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "^P"
pushes Sy Status History No sheet
.It Ic "^X"
evalutes Python expression and pushes sheet for browsing resulting Python object
.It Ic "^Y  z^Y"
pushes sheet for of current row/cell as Python object
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
dives further into Python object
.It Ic "\&."
toggles whether methods and hidden properties are shown

.El
.Sh VisiData Sheets
.Bl -tag -width Xx -compact

.It Sy Static Sheets
.It Sy " \&."
.Sy Clipboard Sheet (Shift-B)
.It Sy " \&."
.Sy Columns Sheet (Shift-C)
.It Sy " \&."
.Sy Commandlog Sheet (Shift-D)
.It Sy " \&."
.Sy Error Sheet (^E)
.It Sy " \&."
.Sy Options Sheet (Shift-O)
.It Sy " \&."
.Sy Sheets Sheet (Shift-S) No "     view, traverse and join sheets"
.It Sy " \&."
.Sy Status History Sheet (^P)
.It Sy " \&."
.Sy Tasks Sheet (^T)

.It Sy Derived Sheets
.It Sy " \&."
.Sy Describe Sheet (Shift-I)
.It Sy " \&."
.Sy Frequency Table (Shift-F)
.It Sy " \&."
.Sy Melted Sheet (Shift-M)
.It Sy " \&."
.Sy Pivot Sheet (Shift-W)

.El

.Sh Columns Sheet (Shift-C)
Properties of columns on the source sheet can be changed with standard editing commands
.No ( Ns Sy e  ge g= Del Ns ) on the Columns Sheet . multiple aggregators can be set by listing them (separated by spaces) in the aggregators column.  The 'g' commands affect the selected rows, which are actually the literal columns on the source sheet.
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
.Sh Commandlog Sheet (Shift-D)
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " x"
replays command in current row
.It Ic "gx"
replays contents of entire commandlog
.El
.Sh Options Sheet (Shift-O)
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
edits option
.El
.Sh Sheets Sheet (Shift-S)
.Bl -tag -width XXXXXXXXXXXXXXX -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
jumps to sheet referenced in current row
.It Ic "&" Ar jointype No
.No where Ar jointype No is one of: 
.El
.Bl -tag -width x -compact -offset XXXXXXXXXXXXXXXXXXXX 
.It Sy "\&."
.Sy inner No " keeps only rows which match keys on all sheets"
.It Sy "\&."
.Sy outer No " keeps all rows from first selected sheet"
.It Sy "\&."
.Sy full No "  keeps all rows from all sheets (union)"
.It Sy "\&."
.Sy diff No "  keeps only rows NOT in all sheets "
.It Sy "\&."
.Sy append No "combines rows of selected sheets into single sheet"
.El
.Sh Describe Sheet (Shift-I)
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "zs  zt  zu"
selects/toggles/unselects rows on source sheet which are being described in current cell
.It Ic " Enter"
pushes a Sy Frequency Table No sheet grouped on column referenced in current row
.It Ic "zEnter"
pushes copy of source sheet with rows described in current cell
.El
.Sh Frequency Table (Shift-F)
Groups rows by key, including columns for each aggregation of a source column.  Set aggregators on columns with '+' (or by 'e'dit on its 'C'olumns sheet) before pressing Shift-F to use the current column as the key.
.Sy gF No groups by all key columns on the source sheet.
.Sy zF No provides summary aggregation without groupingsheet which are being described in current cell
.It Ic "w"
for histograms of numeric value, toggles between bins with an even interval width and bins with an even frequency height
.El
.Sh Melted Sheet (Shift-M)
Pushes melted sheet (unpivot), with all non-key columns reduced to Variable-Value rows.
.Sh Pivot Sheet (Shift-W)
Set key column(s) and aggregators on column(s) before pressing Shift-W on the column to pivot.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Enter
pushes sheet of source rows which comprise current pivot cell
.El

