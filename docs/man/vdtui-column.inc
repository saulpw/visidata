.Ss Column Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " _" Ns " (underscore)"
adjusts width of current column
.It Ic "g_" Ns " (underscore)"
adjusts width of all visible columns
.Pp
.It Ic - Ns " (hyphen)"
hides current column (to unhide, go to
.Sy C Ns olumns sheet and Sy e Ns dit its width)
.It Ic \&! Ns
pins current column to the left as a key column
.It Ic ^
edits name of current column
.It Ic "~  #  %  $  @"
sets type of current column to str/int/float/currency/date
.Pp
.It Ic " =" Ar expr
.No creates new column from Python Ar expr Ns , with column names as variables
.It Ic "g=" Ar expr
.No sets current column for selected rows to result of Python Ar expr
.El
