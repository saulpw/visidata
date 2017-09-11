.Sh Row Selection
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " s   u   Space"
selects/unselects/toggles current row
.It Ic "gs  gu  gSpace"
selects/unselects/toggles all rows
.It Ic " |   \e\ "
selects/unselects rows matching by regex in current column
.It Ic "g|  g\e\"
selects/unselects rows matching by regex in any visible column
.It Ic " \&,"
selects rows matching current cell in current column
.It Ic "g\&,"
selects rows matching in all visible columns
.
.El
.
.
.Sh Row Manipulation
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " [   ]"
sorts ascending/descending by current column
.It Ic "g[  g]"
sorts ascending/descending by all key columns
.It Ic " \&""
opens duplicate sheet with only selected rows
.It Ic "g\&""
opens duplicate sheet with all rows
.El
