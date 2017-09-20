.Bl -tag -width XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -compact
.It Sy "encoding           " No "utf-8"
as passed to codecs.open 
.It Sy "encoding_errors    " No "surrogateescape"
as passed to codecs.open 
.It Sy "regex_flags        " No "I"
flags to pass to re.compile() [AILMSUX] 
.It Sy "default_width      " No "20"
default column width 
.It Sy "textwrap           " No "True"
wrap text to fit window width on TextSheet 
.It Sy "cmd_after_edit     " No "j"
command keystroke to execute after successful edit 
.It Sy "aggr_null_filter   " No "none"
invalid values to filter out when aggregating: (n/e/f/"") 
.It Sy "force_valid_colnames" No "False"
clean column names to be valid Python identifiers 
.It Sy "debug              " No "False"
exit on error and display stacktrace 
.It Sy "curses_timeout     " No "100"
curses timeout in ms 
.It Sy "num_colors         " No "0"
force number of colors to use 
.It Sy "disp_none          " No ""
visible contents of a cell whose value was None 
.It Sy "disp_truncator     " No "…"
indicator that the contents are only partially visible 
.It Sy "disp_oddspace      " No "·"
displayable character for odd whitespace 
.It Sy "disp_unprintable   " No "."
substitute character for unprintables 
.It Sy "disp_column_sep    " No "|"
separator between columns 
.It Sy "disp_keycol_sep    " No "‖"
separator between keys and rest of columns 
.It Sy "disp_status_fmt    " No "{sheet.name}| "
status line prefix 
.It Sy "disp_status_sep    " No " | "
separator between statuses 
.It Sy "disp_edit_fill     " No "_"
edit field fill character 
.It Sy "disp_more_left     " No "<"
header note indicating more columns to the left 
.It Sy "disp_more_right    " No ">"
header note indicating more columns to the right 
.It Sy "disp_error_val     " No "¿"
displayed contents for computation exception 
.It Sy "disp_ambig_width   " No "1"
width to use for unicode chars marked ambiguous 
.It Sy "color_default      " No "normal"
the default color 
.It Sy "color_default_hdr  " No "bold underline"
color of the column headers 
.It Sy "color_current_row  " No "reverse"
color of the cursor row 
.It Sy "color_current_col  " No "bold"
color of the cursor column 
.It Sy "color_current_hdr  " No "reverse underline"
color of the header for the cursor column 
.It Sy "color_column_sep   " No "246 blue"
color of column separators 
.It Sy "color_key_col      " No "81 cyan"
color of key columns 
.It Sy "color_selected_row " No "215 yellow"
color of selected rows 
.It Sy "color_status       " No "bold"
status line color 
.It Sy "color_edit_cell    " No "normal"
edit cell color 
.It Sy "disp_pending       " No ""
string to display in pending cells 
.It Sy "note_pending       " No "⌛"
note to display for pending cells 
.It Sy "note_format_exc    " No "?"
cell note for an exception during type conversion or formatting 
.It Sy "note_getter_exc    " No "!"
cell note for an exception during computation 
.It Sy "color_note_pending " No "bold magenta"
color of note of pending cells 
.It Sy "color_note_type    " No "226 green"
cell note for numeric types in anytype columns 
.It Sy "color_format_exc   " No "48 bold yellow"
color of formatting exception note 
.It Sy "color_getter_exc   " No "red bold"
color of computation exception note 
.El