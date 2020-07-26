.Dd July 23, 2020
.Dt vd \&1 "Quick Reference Guide"
.Os Linux/MacOS
.
.\" Long option with arg: .Lo f filetype format
.\" Long flag: .Lo f filetype
.de Lo
.It Cm -\\$1 Ns , Cm --\\$2 Ns = Ns Ar \\$3
..
.de Lf
.It Cm -\\$1 Ns , Cm --\\$2
..
.Sh NAME
.
.Nm VisiData
.Nd a terminal utility for exploring and arranging tabular data
.
.Sh SYNOPSIS
.
.Nm vd
.Op Ar options
.Op Ar input No ...
.
.Nm vd
.Op Ar options
.Cm --play Ar cmdlog
.Op Cm -w Ar waitsecs
.Op Cm --batch
.Op Cm -o Ar output
.Op Ar field Ns Cm = Ns Ar value
.
.Nm vd
.Op Ar options
.Op Ar input No ...
.Cm + Ns Ar toplevel Ns : Ns Ar subsheet Ns : Ns Ar col Ns : Ns Ar row
.
.Sh DESCRIPTION
.Nm VisiData No is an easy-to-use multipurpose tool to explore, clean, edit, and restructure data.
Rows can be selected, filtered, and grouped; columns can be rearranged, transformed, and derived via regex or Python expressions; and workflows can be saved, documented, and replayed.
.
.Ss REPLAY MODE
.Bl -tag -width XXXXXXXXXXXXXXXXXXXXXX -compact
.Lo p play cmdlog
.No replay a saved Ar cmdlog No within the interface
.
.Lo w replay-wait seconds
.No wait Ar seconds No between commands
.
.Lf b batch
replay in batch mode (with no interface)
.
.Lo o output file
.No save final visible sheet to Ar file No as .tsv
.
.It Sy --replay-movement
.No toggle Sy --play No to move cursor cell-by-cell
.It Ar field Ns Cm = Ns Ar value
.No replace \&"{ Ns Ar field Ns }\&" in Ar cmdlog No contents with Ar value
.El
.
.Ss Commands During Replay
.Bl -tag -width XXXXXXXXXXXXXXXXXXX -compact -offset XXX
.It Sy ^U
pause/resume replay
.It Sy ^N
execute next row in replaying sheet
.It Sy ^K
cancel current replay
.El
.
.Ss GLOBAL COMMANDS
.No All keystrokes are case sensitive. The Sy ^ No prefix is shorthand for Sy Ctrl Ns .
.Pp
.Ss Keystrokes to start off with
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " ^Q"
abort program immediately
.It Ic " ^C"
cancel user input or abort all async threads on current sheet
.It Ic "g^C"
abort all secondary threads
.It Ic "  q"
quit current sheet
.It Ic " gq"
quit all sheets (clean exit)
.Pp
.It Ic " ^H"
view this man page
.It Ic "z^H"
view sheet of command longnames and keybindings
.It Ic "Space" Ar longname
.No execute command by its Ar longname
.Pp
.It Ic "  U"
.No undo the most recent modification ( requires enabled Sy options.undo Ns )
.It Ic "  R"
.No redo the most recent undo ( requires enabled Sy options.undo Ns )
.El
.Ss "Cursor Movement"
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "Arrow PgUp Home"
go as expected
.It Ic " h   j   k   l"
go left/down/up/right
.It Ic "gh  gj  gk  gl"
go all the way to the left/bottom/top/right of sheet
.It Ic "     G  gg"
go all the way to the bottom/top of sheet
.It Ic "^B  ^F"
scroll one page back/forward
.It Ic "zz"
scroll current row to center of screen
.Pp
.It Ic "^^" No (Ctrl+^)
jump to previous sheet (swaps with current sheet)
.Pp
.It Ic  " /   ?" Ar regex
.No search for Ar regex No forward/backward in current column
.It Ic  "g/  g?" Ar regex
.No search for Ar regex No forward/backward over all visible columns
.It Ic  "z/  z?" Ar expr
.No search by Python Ar expr No forward/backward in current column (with column names as variables)
.It Ic  " n   N"
go to next/previous match from last regex search
.Pp
.It Ic  " <   >"
go up/down current column to next value
.It Ic  "z<  z>"
go up/down current column to next null value
.It Ic " {   }"
go up/down current column to next selected row
.
.El
.Pp
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.Pp
.It Ic " c" Ar regex
.No go to next column with name matching Ar regex
.It Ic " r" Ar regex
.No go to next row with key matching Ar regex
.It Ic "zc  zr" Ar number
.No go to column/row Ar number No (0-based)
.Pp
.It Ic " H   J   K   L"
slide current row/column left/down/up/right
.It Ic "gH  gJ  gK  gL"
slide current row/column all the way to the left/bottom/top/right of sheet
.It Ic "zH  zJ  zK  zK" Ar number
.No slide current row/column Ar number No positions to the left/down/up/right
.Pp
.It Ic "zh  zj  zk  zl"
scroll one left/down/up/right
.El
.
.Ss Column Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "  _" Ns " (underscore)"
toggle width of current column between full and default width
.It Ic " g_"
toggle widths of all visible columns between full and default width
.It Ic " z_" Ar number
.No adjust width of current column to Ar number
.It Ic "gz_" Ar number
adjust widths of all visible columns to Ar number
.Pp
.It Ic " -" Ns " (hyphen)"
hide current column
.It Ic "z-" Ns
reduce width of current column by half
.It Ic "gv" Ns
unhide all columns
.Pp
.It Ic "! z!" Ns
toggle/unset current column as a key column
.It Ic "~  #  %  $  @  z#"
set type of current column to str/int/float/currency/date/len
.It Ic "  ^"
edit name of current column
.It Ic " g^"
set names of all unnamed visible columns to contents of selected rows (or current row)
.It Ic " z^"
set name of current column to combined contents of current cell in selected rows (or current row)
.It Ic "gz^"
set name of all visible columns to combined contents of current column for selected rows (or current row)
.Pp
.It Ic "  =" Ar expr
.No create new column from Python Ar expr Ns , with column names as variables
.It Ic " g=" Ar expr
.No set current column for selected rows to result of Python Ar expr
.It Ic "gz=" Ar expr
.No set current column for selected rows to the items in result of Python sequence Ar expr
.It Ic " z=" Ar expr
.No evaluate Python expression on current row and set current cell with result of Python Ar expr
.Pp
.It "  i" (iota)
.No add column with incremental values
.It " gi"
.No set current column for selected rows to incremental values
.It " zi" Ar step
.No add column with values at increment Ar step
.It "gzi" Ar step
.No set current column for selected rows at increment Ar step
.El
.Pp
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " '" Ns " (tick)"
add a frozen copy of current column with all cells evaluated
.It Ic "g'"
open a frozen copy of current sheet with all visible columns evaluated
.It Ic "z'  gz'"
add/reset cache for current/all visible column(s)
.Pp
.It Ic " \&:" Ar regex
.No add new columns from Ar regex No split; number of columns determined by example row at cursor
.It Ic " \&;" Ar regex
.No add new columns from capture groups of Ar regex No (also requires example row)
.It Ic "z" Ns Ic "\&;" Ar expr
.No create new column from bash Ar expr Ns , with Sy $ Ns columnNames as variables
.It Ic " *" Ar regex Ns Sy / Ns Ar subst
.No add column derived from current column, replacing Ar regex No with Ar subst No (may include Sy \e1 No backrefs)
.It Ic "g*  gz*" Ar regex Ns Sy / Ns Ar subst
.No modify selected rows in current/all visible column(s), replacing Ar regex No with Ar subst No (may include Sy \e1 No backrefs)
.Pp
.It Ic " (   g("
.No expand current/all visible column(s) of lists (e.g. Sy [3] Ns ) or dicts (e.g. Sy {3} Ns ) fully
.It Ic "z(  gz(" Ar depth
.No expand current/all visible column(s) of lists (e.g. Sy [3] Ns ) or dicts (e.g. Sy {3} Ns ) to given Ar depth ( Ar 0 Ns = fully)
.It Ic " )"
unexpand current column; restore original column and remove other columns at this level
.It Ic "zM"
.No row-wise expand current column of lists (e.g. Sy [3] Ns ) or dicts (e.g. Sy {3} Ns ) within that column
.El
.Ss Row Selection
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "  s   t   u"
select/toggle/unselect current row
.It Ic " gs  gt  gu"
select/toggle/unselect all rows
.It Ic " zs  zt  zu"
select/toggle/unselect all rows from top to cursor
.It Ic "gzs gzt gzu"
select/toggle/unselect all rows from cursor to bottom
.It Ic " |   \e\ " Ns Ar regex
.No select/unselect rows matching Ar regex No in current column
.It Ic "g|  g\e\ " Ns Ar regex
.No select/unselect rows matching Ar regex No in any visible column
.It Ic "z|  z\e\ " Ns Ar expr
.No select/unselect rows matching Python Ar expr No in any visible column
.It Ic " \&," Ns " (comma)"
select rows matching current cell in current column
.It Ic "g\&,"
select rows matching current row in all visible columns
.
.El
.
.
.Ss Row Sorting/Filtering
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic "  [    ]"
sort ascending/descending by current column; replace any existing sort criteria
.It Ic " g[   g]"
sort ascending/descending by all key columns; replace any existing sort criteria
.It Ic " z[   z]"
sort ascending/descending by current column; add to existing sort criteria
.It Ic "gz[  gz]"
sort ascending/descending by all key columns; add to existing sort criteria
.It Ic " \&""
open duplicate sheet with only selected rows
.It Ic "g\&""
open duplicate sheet with all rows
.It Ic "gz\&""
open duplicate sheet with deepcopy of selected rows
.El
.Ss Editing Rows and Cells
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "  a   za"
append a blank row/column; appended columns cannot be copied to clipboard
.It Ic " ga  gza" Ar number
.No append Ar number No blank rows/columns
.It Ic "  d   gd"
delete (cut) current/selected row(s) and move to clipboard
.It Ic "  y   gy"
yank (copy) current/all selected row(s) to clipboard
.It Ic " zy  gzy"
yank (copy) contents of current column for current/selected row(s) to clipboard
.It Ic " zd  gzd"
delete (cut) contents of current column for current/selected row(s) and move to clipboard
.It Ic "  p    P"
paste clipboard rows after/before current row
.It Ic " zp  gzp"
set cells of current column for current/selected row(s) to last clipboard value
.It Ic "  Y   gY"
.No yank (copy) current/all selected row(s) to system clipboard (using Sy options.clipboard_copy_cmd Ns )
.It Ic " zY  gzY"
.No yank (copy) contents of current column for current/selected row(s) to system clipboard (using Sy options.clipboard_copy_cmd Ns )
.It Ic "  f"
fill null cells in current column with contents of non-null cells up the current column
.
.
.It Ic "  e" Ar text
edit contents of current cell
.It Ic " ge" Ar text
.No set contents of current column for selected rows to Ar text
.
.El
.
.Ss "  Commands While Editing Input"
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter  ^C"
accept/abort input
.It Ic ^O
open external $EDITOR to edit contents
.It Ic ^R
reload initial value
.It Ic "^A  ^E"
go to beginning/end of line
.It Ic "^B  ^F"
go back/forward one character
.It Ic "^←  ^→" No (arrow)
go back/forward one word
.It Ic "^H  ^D"
delete previous/current character
.It Ic ^T
transpose previous and current characters
.It Ic "^U  ^K"
clear from cursor to beginning/end of line
.It Ic "^Y"
paste from cell clipboard
.It Ic "Backspace  Del"
delete previous/current character
.It Ic Insert
toggle insert mode
.It Ic "Up  Down"
set contents to previous/next in history
.It Ic "Tab  Shift+Tab"
autocomplete input (when available)
.
.El
.
.Ss Data Toolkit
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " o" Ar input
open
.Ar input No in Sy VisiData
.It Ic "^S g^S" Ar filename
.No save current/all sheet(s) to Ar filename No in format determined by extension (default .tsv)
.It ""
.No Note: if the format does not support multisave, or the Ar filename No ends in a Sy / Ns , a directory will be created.
.It Ic "z^S" Ar filename
.No save current column only to Ar filename No in format determined by extension (default .tsv)
.It Ic "^D" Ar filename.vd
.No save Sy CommandLog No to Ar filename.vd No file
.It Ic "A"
.No open new blank sheet with one column
.It Ic "T"
.No open new sheet that has rows and columns of current sheet transposed
.Pp
.It Ic " +" Ar aggregator
.No add Ar aggregator No to current column (see Sy "Frequency Table" Ns )
.It Ic "z+" Ar aggregator
.No display result of Ar aggregator No over values in selected rows for current column
.It Ic " &"
.No concatenate top two sheets in Sy Sheets Stack No
.It Ic "g&"
.No concatenate all sheets in Sy Sheets Stack No
.Pp
.El
.Ss Data Visualization
.Bl -tag -width XXXXXXXXXXXXX -compact
.It Ic " ." No (dot)
.No plot current numeric column vs key columns. The numeric key column is used for the x-axis; categorical key column values determine color.
.It Ic "g."
.No plot a graph of all visible numeric columns vs key columns.
.Pp
.El
.No If rows on the current sheet represent plottable coordinates (as in .shp or vector .mbtiles sources),
.Ic " ." No plots the current row, and Ic "g." No plots all selected rows (or all rows if none selected).
.Ss "  Canvas-specific Commands"
.Bl -tag -width XXXXXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " +   -"
increase/decrease zoom level, centered on cursor
.It Ic " _" No (underscore)
zoom to fit full extent
.It Ic "z_" No (underscore)
set aspect ratio
.It Ic " x" Ar xmin xmax
.No set Ar xmin Ns / Ns Ar xmax No on graph
.It Ic " y" Ar ymin ymax
.No set Ar ymin Ns / Ns Ar ymax No on graph
.It Ic " s   t   u"
select/toggle/unselect rows on source sheet contained within canvas cursor
.It Ic "gs  gt  gu"
select/toggle/unselect rows on source sheet visible on screen
.It Ic " d"
delete rows on source sheet contained within canvas cursor
.It Ic "gd"
delete rows on source sheet visible on screen
.It Ic " Enter"
open sheet of source rows contained within canvas cursor
.It Ic "gEnter"
open sheet of source rows visible on screen
.It Ic " 1" No - Ic "9"
toggle display of layers
.It Ic "^L"
redraw all pixels on canvas
.It Ic " v"
.No toggle Ic show_graph_labels No option
.It Ic "mouse scrollwheel"
zoom in/out of canvas
.It Ic "left click-drag"
set canvas cursor
.It Ic "right click-drag"
scroll canvas
.El
.Ss Split Screen
.Bl -tag -width XXXXXXXXXXXXX -compact
.It Ic " Z"
.No split screen in half, so that second sheet on the stack is visible in a second pane
.It Ic "zZ"
.No split screen, and queries for height of second pane
.El
.Ss "  Split Window specific Commands"
.Bl -tag -width XXXXXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "gZ"
.No close an already split screen, current pane full screens
.It Ic "Tab"
.No jump to other pane
.It Ic "^^" No (Ctrl+^)
.No swap which sheet is in current pane
.Pp
.El
.Ss Other Commands
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic "Q"
.No quit current sheet and remove it from the Sy CommandLog
.It Ic "v"
toggle sheet-specific visibility (multi-line rows on Sheet, legends/axes on Graph)
.Pp
.Pp
.It Ic " ^E  g^E"
view traceback for most recent error(s)
.It Ic "z^E"
view traceback for error in current cell
.Pp
.It Ic " ^L"
refresh screen
.It Ic " ^R"
reload current sheet
.It Ic "z^R"
clear cache for current column
.It Ic " ^Z"
suspend VisiData process
.It Ic " ^G"
show cursor position and bounds of current sheet on status line
.It Ic " ^V"
show version and copyright information on status line
.It Ic " ^P"
.No open Sy Status History
.
.El
.Pp
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.It Ic " ^Y  z^Y  g^Y"
open current row/cell/sheet as Python object
.It Ic " ^X" Ar expr
.No evaluate Python Ar expr No and opens result as Python object
.It Ic "z^X" Ar expr
.No evaluate Python Ar expr Ns , in context of current row, and open result as Python object
.It Ic "g^X" Ar stmt
.No execute Python Ar stmt No in the global scope
.El
.
.Ss Internal Sheets List
.Bl -tag -width Xx -compact
.It Sy " \&."
.Sy VisiDataMenu No (Shift+V) "     browse list of core sheets"
.It Sy " \&."
.Sy Directory Sheet No "            browse properties of files in a directory"
.It Sy " \&."
.Sy Plugins Sheet No "              browse, install, and (de)activate plugins"
.It " "
.It Sy Metasheets
.It Sy " \&."
.Sy Columns Sheet No (Shift+C) "    edit column properties"
.It Sy " \&."
.Sy Sheets Sheet No (Shift+S) "     jump between sheets or join them together"
.It Sy " \&."
.Sy Options Sheet No (Shift+O) "    edit configuration options"
.It Sy " \&."
.Sy Commandlog No (Shift+D) "       modify and save commands for replay"
.It Sy " \&."
.Sy Error Sheet No (Ctrl+E) "           view last error"
.It Sy " \&."
.Sy Status History No (Ctrl+P) "        view history of status messages"
.It Sy " \&."
.Sy Threads Sheet No (Ctrl+T) "         view, cancel, and profile asynchronous threads"
.Pp
.It Sy Derived Sheets
.It Sy " \&."
.Sy Frequency Table No (Shift+F) "  group rows by column value, with aggregations of other columns"
.It Sy " \&."
.Sy Describe Sheet No (Shift+I) "   view summary statistics for each column"
.It Sy " \&."
.Sy Pivot Table No (Shift+W) "      group rows by key and summarize current column"
.It Sy " \&."
.Sy Melted Sheet No (Shift+M) "     unpivot non-key columns into variable/value columns"
.It Sy " \&."
.Sy Transposed Sheet No (Shift+T) "  open new sheet with rows and columns transposed"
.El
.
.Ss INTERNAL SHEETS
.Ss VisiDataMenu (Shift+V)
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Enter
.No load sheet in current row
.El
.Ss Directory Sheet
.Bl -inset -compact
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Space Ar open-dir-current
.No open the Sy Directory Sheet No for the current directory
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter  gEnter"
open current/selected file(s) as new sheet(s)
.It Ic " ^O  g^O"
open current/selected file(s) in external $EDITOR
.It Ic " ^R  z^R  gz^R"
reload information for all/current/selected file(s)
.El
.
.Ss Plugins Sheet
.Bl -inset -compact
.It Browse through a list of available plugins. VisiData needs to be restarted before plugin activation takes effect. Installation may require internet access.
.El
.Bl -inset -compact
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Space Ar open-plugins
.No open the Sy Plugins Sheet
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "a"
install and activate current plugin
.It Ic "d"
deactivate current plugin
.El
.Ss METASHEETS
.Ss Columns Sheet (Shift+C)
.Bl -inset -compact
.It Properties of columns on the source sheet can be changed with standard editing commands ( Ns Sy e  ge g= Del Ns ) on the Sy Columns Sheet Ns . Multiple aggregators can be set by listing them (separated by spaces) in the aggregators column.  The 'g' commands affect the selected rows, which are the literal columns on the source sheet.
.El
.Bl -inset -compact
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic gC
.No open Sy Columns Sheet No with all visible columns from all sheets
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " &"
add column from concatenating selected source columns
.It Ic "g! gz!"
toggle/unset selected columns as key columns on source sheet
.It Ic "g+" Ar aggregator
add Ar aggregator No to selected source columns
.It Ic "g-" No (hyphen)
hide selected columns on source sheet
.It Ic "g~ g# g% g$ g@  gz#"
set type of selected columns on source sheet to str/int/float/currency/date/len
.It Ic " Enter"
.No open a Sy Frequency Table No sheet grouped by column referenced in current row
.El
.
.Ss Sheets Sheet (Shift+S)
.Bl -inset -compact
.It open Sy Sheets Stack Ns , which contains only the active sheets on the current stack
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic gS
.No open Sy Sheets Sheet Ns , which contains all sheets from current session, active and inactive
.It Ic "Alt" Ar number
.No jump to sheet Ar number Ns
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " Enter"
jump to sheet referenced in current row
.It Ic "gEnter"
push selected sheets to top of sheet stack
.It Ic " a"
add row to reference a new blank sheet
.It Ic "gC  gI"
.No open Sy Columns Sheet Ns / Ns Sy Describe Sheet No with all visible columns from selected sheets
.It Ic "g^R"
.No reload all selected sheets
.It Ic "z^C  gz^C"
abort async threads for current/selected sheets(s)
.It Ic " &" Ar jointype
.No merge selected sheets with visible columns from all, keeping rows according to Ar jointype Ns :
.El
.Bl -tag -width x -compact -offset XXXXXXXXXXXXXXXXXXXX
.It Sy "\&."
.Sy inner No " keep only rows which match keys on all sheets"
.It Sy "\&."
.Sy outer No " keep all rows from first selected sheet"
.It Sy "\&."
.Sy full No "  keep all rows from all sheets (union)"
.It Sy "\&."
.Sy diff No "  keep only rows NOT in all sheets"
.It Sy "\&."
.Sy append No "keep all rows from all sheets (concatenation)"
.It Sy "\&."
.Sy extend No "copy first selected sheet, keeping all rows and sheet type, and extend with columns from other sheets"
.It Sy "\&."
.Sy merge No " mostly keep all rows from first selected sheet, except prioritise cells with non-null/non-error values"
.El
.
.Ss Options Sheet (Shift+O)
.Bl -inset -compact
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic Shift+O
.No edit global options (apply to Sy all sheets Ns )
.It Ic zO
.No edit sheet options (apply to Sy current sheet No only)
.It Ic gO
.No open Sy options.config No as Sy TextSheet No
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "Enter  e"
edit option at current row
.El
.
.Ss CommandLog (Shift+D)
.Bl -inset -compact
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic  D
.No open current sheet's Sy CommandLog No with all other loose ends removed; includes commands from parent sheets
.It Ic gD
.No open global Sy CommandLog No for all commands executed in the current session
.It Ic zD
.No open current sheet's Sy CommandLog No with the parent sheets commands' removed
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "  x"
replay command in current row
.It Ic " gx"
replay contents of entire CommandLog
.It Ic " ^C"
abort replay
.El
.
.Ss DERIVED SHEETS
.Ss Frequency Table (Shift+F)
.Bl -inset -compact
.It A Sy Frequency Table No groups rows by one or more columns, and includes summary columns for those with aggregators.
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic gF
open Frequency Table, grouped by all key columns on source sheet
.It Ic zF
open one-line summary for all rows and selected rows
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " s   t   u"
select/toggle/unselect these entries in source sheet
.It Ic " Enter  gEnter"
open copy of source sheet with rows that are grouped in current cell / selected rows
.El
.
.Ss Describe Sheet (Shift+I)
.Bl -inset -compact
.It A Sy Describe Sheet No contains descriptive statistics for all visible columns.
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic gI
.No open Sy Describe Sheet No for all visible columns on all sheets
.El
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "zs  zu"
select/unselect rows on source sheet that are being described in current cell
.It Ic " !"
toggle/unset current column as a key column on source sheet
.It Ic " Enter"
.No open a Sy Frequency Table No sheet grouped on column referenced in current row
.It Ic "zEnter"
open copy of source sheet with rows described in current cell
.El
.
.Ss Pivot Table (Shift+W)
.Bl -inset -compact
.It Set key column(s) and aggregators on column(s) before pressing Sy Shift+W No on the column to pivot.
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " Enter"
open sheet of source rows aggregated in current pivot row
.It Ic "zEnter"
open sheet of source rows aggregated in current pivot cell
.El
.Ss Melted Sheet (Shift+M)
.Bl -inset -compact
.It Open Melted Sheet (unpivot), with key columns retained and all non-key columns reduced to Variable-Value rows.
.It (global commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic "gM" Ar regex
.No open Melted Sheet (unpivot), with key columns retained and Ar regex No capture groups determining how the non-key columns will be reduced to Variable-Value rows.
.El
.Ss Python Object Sheet (^X ^Y g^Y z^Y)
.Bl -inset -compact
.It (sheet-specific commands)
.El
.Bl -tag -width XXXXXXXXXXXXXXX -compact -offset XXX
.It Ic " Enter"
dive further into Python object
.It Ic " v"
toggle show/hide for methods and hidden properties
.It Ic "gv  zv"
show/hide methods and hidden properties
.El
.
.Sh COMMANDLINE OPTIONS
.Bl -tag -width XXXXXXXXXXXXXXXXXXXXXXXXXXX -compact
.It Cm -P Ns = Ns Ar longname
.No preplay Ar longname No before replay or regular launch; limited to Sy Base Sheet No bound commands
.It Cm + Ns Ar toplevel Ns : Ns Ar subsheet Ns : Ns Ar col Ns : Ns Ar row
.No launch vd with Ar subsheet No of Ar toplevel No at top-of-stack, and cursor at Ar col No and Ar row Ns ; all arguments are optional
.Pp
.Lo f filetype filetype
.No "tsv               "
set loader to use for
.Ar filetype
instead of file extension
.
.Lo y confirm-overwrite F
.No "True              "
overwrite existing files without confirmation
.
.
.El
.so vd-cli.inc
.
.Ss DISPLAY OPTIONS
.No Display options can only be set via the Sx Options Sheet No or a Pa .visidatarc No (see Sx FILES Ns ).
.Pp
.
.so vd-opts.inc
.
.Sh EXAMPLES
.Dl Nm vd Cm foo.tsv
.No open the file foo.tsv in the current directory
.Pp
.Dl Nm vd Cm -f sqlite bar.db
.No open the file bar.db as a sqlite database
.Pp
.Dl Nm vd Cm -b countries.fixed -o countries.tsv
.No convert countries.fixed (in fixed width format) to countries.tsv (in tsv format)
.Pp
.Dl Nm vd Cm postgres:// Ns Ar username Ns Sy "\&:" Ns Ar password Ns Sy @ Ns Ar hostname Ns Sy  "\&:" Ns Ar port Ns Sy / Ns Ar database
.No open a connection to the given postgres database
.Pp
.Dl Nm vd Cm --play tests/pivot.vd --replay-wait 1 --output tests/pivot.tsv
.No replay tests/pivot.vd, waiting 1 second between commands, and output the final sheet to test/pivot.tsv
.Pp
.Dl Ic ls -l | Nm vd Cm -f fixed --skip 1 --header 0
.No parse the output of ls -l into usable data
.Pp
.Dl Ic ls | vd | lpr
.No interactively select a list of filenames to send to the printer
.Pp
.Dl Ic vd newfile.tsv
.No open a blank sheet named Ar newfile No if file does not exist
.Pp
.Dl Ic vd sample.xlsx +:sheet1:2:3
.No launch with Sy sheet1 No at top-of-stack, and cursor at column Sy 2 No and row Sy 3 No
.Pp
.Dl Ic vd -P open-plugins
.No preplay longname Sy open-plugins No before starting the session
.Sh FILES
At the start of every session,
.Sy VisiData No looks for Pa $HOME/.visidatarc Ns , and calls Python exec() on its contents if it exists.
For example:
.Bd -literal
   options.min_memory_mb=100  # stop processing without 100MB free

   bindkey('0', 'go-leftmost')   # alias '0' to go to first column, like vim

   def median(values):
       L = sorted(values)
       return L[len(L)//2]

   aggregator('median', median)
.Ed
.Pp
Functions defined in .visidatarc are available in python expressions (e.g. in derived columns).
.
.Sh SUPPORTED SOURCES
These are the supported sources:
.Pp
.Bl -inset -compact -offset xxx
.It Sy tsv No (tab-separated value)
.Bl -inset -compact -offset xxx
.It Plain and simple.  Nm VisiData No writes tsv format by default.  See the Sy --tsv-delimiter No option.
.El
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy csv No (comma-separated value)
.Bl -inset -compact -offset xxx
.It .csv files are a scourge upon the earth, and still regrettably common.
.It See the Sy --csv-dialect Ns , Sy --csv-delimiter Ns , Sy --csv-quotechar Ns , and Sy --csv-skipinitialspace No options.
.It Accepted dialects are Ic excel-tab Ns , Ic unix Ns , and Ic excel Ns .
.El
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy fixed No (fixed width text)
.Bl -inset -compact -offset xxx
.It Columns are autodetected from the first 1000 rows (adjustable with Sy --fixed-rows Ns ).
.El
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy json No (single object) and Sy jsonl Ns / Ns Sy ndjson Ns / Ns Sy ldjson No (one object per line).
.Bl -inset -compact -offset xxx
.It Cells containing lists (e.g. Sy [3] Ns ) or dicts ( Ns Sy {3} Ns ) can be expanded into new columns with Sy "\&(" No and unexpanded with Sy "\&)" Ns .
.El
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy yaml Ns / Ns Sy yml No (requires Sy PyYAML Ns )
.Bl -inset -compact -offset xxx
.It Uses the safe YAML loader, which supports the most common uses of YAML.
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy pcap No ( requires Sy dpkt Ns , Sy dnslib Ns )
.Bl -inset -compact -offset xxx
.It View and investigate captured network traffic in a tabular format.
.El
.El
.Pp
.Bl -inset -compact -offset xxx
.It Sy png No (requires Sy pypng Ns )
.Bl -inset -compact -offset xxx
.It Pixels can be edited and saved in data form. Images can be plotted with Ic "\&." No (dot).
.El
.El
.
.Pp
The following URL schemes are supported:
.Bl -inset -compact -offset xxx
.It Sy http No (requires Sy requests Ns ); can be used as transport for with another filetype
.It Sy postgres No (requires Sy psycopg2 Ns )
.El
.
.Pp
.Bl -inset -compact
.It The following sources may include multiple tables.  The initial sheet is the table directory;
.Sy Enter No loads the entire table into memory.
.El
.
.Pp
.Bl -inset -compact -offset xxx
.It Sy sqlite
.It Sy xlsx No (requires Sy openpyxl Ns )
.It Sy xls No (requires Sy xlrd Ns )
.It Sy hdf5 No (requires Sy h5py Ns )
.It Sy ttf Ns / Ns Sy otf No (requires Sy fonttools Ns )
.It Sy mbtiles No (requires Sy mapbox-vector-tile Ns )
.It Sy htm Ns / Ns Sy html No (requires Sy lxml Ns )
.It Sy xml No (requires Sy lxml Ns )
.Bl -tag -width XXXX -compact -offset XXX
.It Sy " v"
show only columns in current row attributes
.It Sy za
add column for xml attribute
.El
.It Sy xpt No (SAS; requires Sy xport Ns )
.It Sy sas7bdat No (SAS; requires Sy sas7bdat Ns )
.It Sy sav No (SPSS; requires Sy savReaderWriter Ns )
.It Sy dta No (Stata; requires Sy pandas Ns )
.It Sy shp No (requires Sy pyshp Ns )
.El
.Pp
In addition,
.Sy .zip Ns , Sy .gz Ns , Sy .bz2 Ns , and Sy .xz No files are decompressed on the fly.
.Pp
.No VisiData has an adapter for Sy pandas Ns . To load a file format which is supported by Sy pandas Ns , pass Sy -f pandas data.foo Ns . This will call Sy pandas.read_foo() Ns .
.Pp
.No For example, Sy vd -f pandas data.parquet No loads a parquet file. Note that when using the Sy pandas No loader, the Sy .fileformat No file extension is mandatory
.
.Sh SUPPORTED OUTPUT FORMATS
These are the supported savers:
.Pp
.Bl -inset -compact -offset xxx
.It Sy tsv No (tab-separated value)
.It Sy csv No (comma-separated value)
.It Sy json No (one object with all rows)
.It Sy jsonl Ns / Ns Sy ndjson Ns / Ns Sy ldjson No (one object per line/row)
.It Sy sqlite No (multisave capable)
.Bl -inset -compact -offset xxx
.It All expanded subcolumns must be closed (with Sy "\&)" Ns ) to retain the same structure.
.It Sy .shp No files can be saved as Sy geoJSON Ns .
.El
.It Sy md No (org-mode compatible markdown table)
.It Sy htm Ns / Ns Sy html No (requires Sy lxml Ns )
.It Sy png No (requires Sy pypng Ns )
.El
.Pp
.No Multisave is supported by Sy html Ns , Sy md Ns , and Sy txt Ns ; Sy g^S No will save all sheets into a single output file.
.Pp
.
.Sh AUTHOR
.Nm VisiData
was made by
.An Saul Pwanson Aq Mt vd@saul.pw Ns .
