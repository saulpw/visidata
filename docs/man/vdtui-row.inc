.Ss Row Selection
.
.Bl -tag -width XXXXXXXXXXXXXXX -compact
.
.It Ic " s   t   u"
selects/toggles/unselects current row
.It Ic "gs  gt  gu"
selects/toggles/unselects all rows
.It Ic " |   \e\ " Ns Ar regex
.No selects/unselects rows matching Ar regex No in current column
.It Ic "g|  g\e\ " Ns Ar regex
.No selects/unselects rows matching Ar regex No in any visible column
.It Ic " \&,"
selects rows matching current cell in current column
.It Ic "g\&,"
selects rows matching this row in all visible columns
.
.El
.
.
.Ss Row Sorting/Filtering
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
