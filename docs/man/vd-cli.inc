.Bl -tag -width XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -compact
.It Sy --encoding Ns = Ns Ar "str              " No "utf-8"
as passed to codecs.open
.It Sy --encoding-errors Ns = Ns Ar "str       " No "surrogateescape"
as passed to codecs.open
.It Sy --regex-flags Ns = Ns Ar "str           " No "I"
flags to pass to re.compile() [AILMSUX]
.It Sy --default-width Ns = Ns Ar "int         " No "20"
default column width
.It Sy --wrap Ns = Ns Ar "bool                 " No "False"
wrap text to fit window width on TextSheet
.It Sy --cmd-after-edit Ns = Ns Ar "str        " No "j"
command keystroke to execute after successful edit
.It Sy --aggr-null-filter Ns = Ns Ar "str      " No "none"
invalid values to filter out when aggregating: (n/e/f/"")
.It Sy --force-valid-colnames Ns = Ns Ar "bool " No "False"
clean column names to be valid Python identifiers
.It Sy --debug Ns = Ns Ar "bool                " No "False"
exit on error and display stacktrace
.It Sy --curses-timeout Ns = Ns Ar "int        " No "100"
curses timeout in ms
.It Sy --num-colors Ns = Ns Ar "int            " No "0"
force number of colors to use
.It Sy --note-pending Ns = Ns Ar "str          " No "⌛"
note to display for pending cells
.It Sy --note-format-exc Ns = Ns Ar "str       " No "?"
cell note for an exception during type conversion or formatting
.It Sy --note-getter-exc Ns = Ns Ar "str       " No "!"
cell note for an exception during computation
.It Sy --profile-tasks Ns = Ns Ar "bool        " No "True"
profile async tasks
.It Sy --min-memory-mb Ns = Ns Ar "int         " No "0"
minimum memory to continue loading and async processing
.It Sy --confirm-overwrite Ns = Ns Ar "bool    " No "True"
whether to prompt for overwrite confirmation on save
.It Sy --headerlines Ns = Ns Ar "int           " No "1"
parse first N rows of .csv/.tsv as column names
.It Sy --skiplines Ns = Ns Ar "int             " No "0"
skip first N lines of text input
.It Sy --filetype Ns = Ns Ar "str              " No ""
specify file type
.It Sy --pyobj-show-hidden Ns = Ns Ar "bool    " No "False"
show methods and _private properties
.It Sy --delay Ns = Ns Ar "float               " No "0.0"
delay between replayed commands, in seconds
.It Sy --regex-maxsplit Ns = Ns Ar "int        " No "0"
maxsplit to pass to regex.split
.It Sy --csv-dialect Ns = Ns Ar "str           " No "excel"
dialect passed to csv.reader
.It Sy --csv-delimiter Ns = Ns Ar "str         " No ","
delimiter passed to csv.reader
.It Sy --csv-quotechar Ns = Ns Ar "str         " No """
quotechar passed to csv.reader
.It Sy --csv-skipinitialspace Ns = Ns Ar "bool " No "True"
skipinitialspace passed to csv.reader
.It Sy --fixed-rows Ns = Ns Ar "int            " No "1000"
number of rows to check for fixed width columns
.El