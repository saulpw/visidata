.so vdtui-main.inc
.so vdtui-cursor.inc
.Pp
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.Pp
.It Ic " c" Ar regex
.No moves to the next column with name matching Ar regex
.It Ic " r" Ar regex
.No moves to the next row with key matching Ar regex
.It Ic "zc  zr" Ar number
.No moves to given column/row Ar number
.Pp
.It Ic " H   J   K   L"
slides current row/column left/down/up/right
.It Ic "gH  gJ  gK  gL"
slides current row/column all the way to the left/bottom/top/right of sheet
.Pp
.It Ic "zh  zj  zk  zl"
scrolls one left/down/up/right
.It Ic "  zt  zz  zb  "
scrolls current row to top/center/bottom of screen
.El
.
.so vdtui-column.inc
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " z=" Ar expr
.No evaluates Python Ar expr No on current row and displays result on status line
.It Ic "gz=" Ar iterable
.No sets selected rows in current column to the results of a Python Ar iterable No
.Pp
.It Ic " g^"
sets names of all visible columns to contents of current row
.It Ic " z^"
sets name of current column to contents of current cell
.It Ic "gz^"
sets name of current column to combined contents of current cell in selected rows
.Pp
.It Ic " '" Ns " (tick)"
adds a frozen copy of current column with all cells evaluated
.
.It Ic "g'"
opens a frozen copy of current sheet with all visible columns evaluated
.Pp
.It Ic "\&:" Ar regex
.No adds new columns from Ar regex No split; # columns determined by example row at cursor
.It Ic "\&;" Ar regex
.No adds new columns from capture groups of Ar regex Ns ; also requires example row
.It Ic "*" Ar regex Ns Sy / Ns Ar subst
.No replaces Ar regex No with Ar subst Ns , which may include backreferences ( Ns Sy \e1 No etc)
.El
.so vdtui-row.inc
.Ss Editing Rows and Cells
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "  a"
appends a blank row
.It Ic " ga" Ar number
.No appends Ar number No blank rows
.It Ic "  d  gd"
deletes current/all selected row(s) and writes to clipboard
.It Ic "  y  gy"
copies current/all selected row(s) to clipboard
.It Ic "  p   Shift-P"
pastes most recent clipboard rows after/before current row
.It Ic "  f"
fills null cells in current column with content of non-null cells up the current column
.
.so vdtui-editing.inc
.
.Ss Data Toolkit
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " o" Ar input
opens
.Ar input No in Sy VisiData
.It Ic "^S" Ar filename
.No saves current sheet to Ar filename No in format determined by extension (default .tsv)
.It Ic "^D" Ar filename.vd
.No saves commandlog to Ar filename.vd No file
.It Ic "Shift-A" Ar number
.No opens new blank sheet with Ar number No columns
.It Ic " m"
.No opens a canvas graphing current column against key column
.It Ic "gm"
.No opens a canvas graphing all visible columns against key column
.It Ic "Shift-R" Ar number
opens duplicate sheet with a random population subset of
.Ar number No rows
.Pp
.It Ic " +" Ar aggregator
.No adds Ar aggregator No to current column (see Sy "Frequency Table" Ns )
.It Ic "z+" Ar aggregator
.No displays result of Ar aggregator No over values in selected rows for current column
.El
.so vdtui-other.inc
.Pp
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "^P"
.No opens Sy Status History
.It Ic "^X"
evalutes Python expression and opens sheet for browsing resulting Python object
.It Ic "^Y  z^Y"
opens sheet of current row/cell as Python object
.El
.
.Ss Internal Sheets List
.Bl -tag -width Xx -compact
.It " "
.It Sy Metasheets
.It Sy " \&."
.Sy Columns Sheet No (Shift-C) "    edit column properties"
.It Sy " \&."
.Sy Sheets Sheet No (Shift-S) "     jump between sheets or join them together"
.It Sy " \&."
.Sy Options Sheet No (Shift-O) "    edit all configurable options"
.It Sy " \&."
.Sy Commandlog No (Shift-D) "       modify and save commands for replay"
.It Sy " \&."
.Sy Error Sheet No (^E) "           view last error"
.It Sy " \&."
.Sy Status History No (^P) "        view history of status messages"
.It Sy " \&."
.Sy Tasks Sheet No (^T) "           view, cancel, and profile asynchronous tasks"
.Pp
.It Sy Derived Sheets
.It Sy " \&."
.Sy Frequency Table No (Shift-F) "  group rows by column value, with aggregations of other columns"
.It Sy " \&."
.Sy Describe Sheet No (Shift-I) "   view summary statistics for each column"
.It Sy " \&."
.Sy Pivot Table No (Shift-W) "      group rows by key and summarize current column"
.It Sy " \&."
.Sy Melted Sheet No (Shift-M) "     unpivot non-key columns into variable/value columns"
.El
.Ss METASHEETS
.Ss Columns Sheet (Shift-C)
.Bl -inset -compact
.It Properties of columns on the source sheet can be changed with standard editing commands ( Ns Sy e  ge g= Del Ns ) on the Sy Columns Sheet Ns . Multiple aggregators can be set by listing them (separated by spaces) in the aggregators column.  The 'g' commands affect the selected rows, which are actually the literal columns on the source sheet.
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " &"
adds column from concatenating selected source columns
.It Ic "g!"
toggles selected columns as keys on source sheet
.It Ic "g+"
adds aggregator to selected source columns
.It Ic "g_" No (underscore)
adjusts widths of selected columns on source sheet
.It Ic "g-" No (hyphen)
hides selected columns on source sheet
.It Ic "g~ g# g% g$ g@"
sets type of selected columns to str/int/float/currency/date
.It Ic " Enter"
.No opens a Sy Frequency Table No sheet grouped on column referenced in current row
.El
.
.Ss Sheets Sheet (Shift-S)
.Bl -inset -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
jumps to sheet referenced in current row
.It Ic "&" Ar jointype
.No merges selected sheets with visible columns from all, keeping rows according to Ar jointype Ns :
.El
.Bl -tag -width x -compact -offset XXXXXXXXXXXXXXXXXXXX 
.It Sy "\&."
.Sy inner No " keeps only rows which match keys on all sheets"
.It Sy "\&."
.Sy left No " keeps all rows from first selected sheet"
.It Sy "\&."
.Sy full No "  keeps all rows from all sheets (union)"
.It Sy "\&."
.Sy diff No "  keeps only rows NOT in all sheets"
.It Sy "\&."
.Sy append No "keeps all rows from all sheets (concatenation)"
.El
.
.Ss Options Sheet (Shift-O)
.Bl -inset -compact 
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
edits option
.El
.
.Ss Commandlog (Shift-D)
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " x"
replays command in current row
.It Ic "gx"
replays contents of entire commandlog
.El
.
.Ss DERIVED SHEETS
.Ss Frequency Table (Shift-F)
.Bl -inset -compact
.It A Sy Frequency Table No groups rows by one or more columns, and includes summary columns for those with aggregators.
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic gF
groups by all key columns on source sheet
.It Ic zF
opens a one-line summary for selected rows
.It (sheet-specific commands)
.It Ic " s   t   u"
selects/toggles/unselects these entries in source sheet
.El
.
.Ss Describe Sheet (Shift-I)
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "zs  zt  zu"
selects/toggles/unselects rows on source sheet which are being described in current cell
.It Ic " Enter"
.No opens a Sy Frequency Table No sheet grouped on column referenced in current row
.It Ic "zEnter"
opens copy of source sheet with rows described in current cell
.El
.
.Ss Pivot Table (Shift-W)
.Bl -inset -compact
.It Set key column(s) and aggregators on column(s) before pressing Sy Shift-W No on the column to pivot.
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " Enter"
opens sheet of source rows which comprise current pivot row
.It Ic "zEnter"
opens sheet of source rows which comprise current pivot cell
.El
.Ss Melted Sheet (Shift-M)
.Bl -inset -compact
.It Opens melted sheet (unpivot), with all non-key columns reduced to Variable-Value rows.
.El
.Ss Python Object Sheet (^X ^Y)
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter"
dives further into Python object
.It Ic "e"
edits contents of current cell
.It Ic "\&." No (period)
toggles whether methods and hidden properties are shown
.El
