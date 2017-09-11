.Sh Column Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic _ Ns " (underscore)"
adjusts width of current column
.It Ic - Ns " (hyphen)"
hides current column (to unhide, go to
.Sy C Ns olumns sheet and Sy e Ns dit its width)
.It Ic \&! Ns
pins current column to the left as a key column
.It Ic ^
edits name of current column
.It Ic "~  #  %  $  @"
sets type of current column to str/int/float/currency/date

.It Ic " ="
creates a new column from given Python expression, which is computed for each row, using column names are as variables
.It Ic "g="
sets value in current column for selected rows to result of given Python expression

.El
