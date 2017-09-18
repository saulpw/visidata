.Sh SUPPORTED SOURCES
.Bl -inset -compact
.It Sy Postgres databases No (requires Sy psycopg2 Ns )
.El
.Bl -inset -compact -offset xxxxxx
.It Sy postgres:// Ns Ar username Ns Sy "\&:" Ns Ar password Ns Sy @ Ns Ar hostname Ns Sy  "\&:" Ns Ar port Ns Sy / Ns Ar database
.It First sheet is list of all user tables; ENTER loads entire table into memory.
.El

.Bl -inset -compact
.It Sy Excel spreadsheets No (requires Sy openpyxl No for .xlsx and Sy xlrd No for .xls files)
.El
.Bl -inset -compact -offset xxxxxx
.It Ar filename.xlsx No
.It Ar filename.xls No
.El
.Bl -inset -compact -offset xx
.It First sheet is list of Excel sheets; ENTER loads entire sheet into memory.
.El
