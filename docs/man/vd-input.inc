.Sh SUPPORTED SOURCES
.Bl -inset -compact
.It Sy tsv No (tab-separated value)
.El
.Bl -inset -compact -offset xxx
.It Plain and simple.  Nm VisiData No writes tsv format by default.
.El
.Pp
.Bl -inset -compact
.It Sy csv No (comma-separated value)
.El
.Bl -inset -compact -offset xxx
.It .csv files are a scourge upon the earth, and still regrettably common.  See the Sy --csv-dialect Ns , Sy --csv-delimiter Ns , Sy --csv-quotechar Ns , and Sy --csv-skipinitialspace No options.
.El
.Pp
.Bl -inset -compact
.It Sy fixed No (fixed width text)
.El
.Bl -inset -compact -offset xxx
.It Columns are autodetected from the first 1000 rows (adjustable with Sy --fixed-rows Ns ).
.El
.Pp
.Bl -inset -compact -offset xxx
.It "  " For these multi-table sources, the first sheet is a directory of tables.
.It "  " Sy Enter No loads the entire table into memory.
.El
.Pp
.Bl -inset -compact -offset xxxxxx
.It Sy sqlite
.It Sy xlsx No (requires Sy openpyxl Ns )
.It Sy xls No (requires Sy xlrd Ns )
.It Sy hdf5 No (requires Sy h5py Ns )
.It Sy postgres No (requires Sy psycopg2 Ns ): 
.El
