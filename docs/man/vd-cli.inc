.It Sy --debug Ns =bool
.No abort on error and display stacktrace (default Sy False Ns )
.It Sy --encoding Ns =str
.No as passed to codecs.open (default Sy utf-8 Ns )
.It Sy --encoding-errors Ns =str
.No as passed to codecs.open (default Sy surrogateescape Ns )
.It Sy --curses-timeout Ns =int
.No curses timeout in ms (default Sy 100 Ns )
.It Sy --default-width Ns =int
.No default column width (default Sy 20 Ns )
.It Sy --regex-flags Ns =str
.No flags to pass to re.compile() [AILMSUX] (default Sy I Ns )
.It Sy --num-colors Ns =int
.No force number of colors to use (default Sy 0 Ns )
.It Sy --textwrap Ns =bool
.No wrap text to fit window width on TextSheet (default Sy True Ns )
.It Sy --cmd-after-edit Ns =str
.No command keystroke to execute after successful edit (default Sy j Ns )
.It Sy --aggr-null-filter Ns =str
.No invalid values to filter out when aggregating: (n/e/f/"") (default Sy none Ns )
.It Sy --force-valid-colnames Ns =bool
.No clean column names to be valid Python identifiers (default Sy False Ns )
.It Sy --float-chars Ns =str
.No valid numeric characters (default Sy +-0123456789.eE_ Ns )
.It Sy --profile-tasks Ns =bool
.No profile async tasks (default Sy True Ns )
.It Sy --min-task-time-s Ns =float
.No only keep tasks that take longer than this number of seconds (default Sy 0.1 Ns )
.It Sy --min-memory-mb Ns =int
.No stop loading and async processing unless this much memory is available (default Sy 0 Ns )
.It Sy --confirm-overwrite Ns =bool
.No whether to prompt for overwrite confirmation on save (default Sy True Ns )
.It Sy --headerlines Ns =int
.No parse first N rows of .csv/.tsv as column names (default Sy 1 Ns )
.It Sy --skiplines Ns =int
.No skip first N lines of text input (default Sy 0 Ns )
.It Sy --filetype Ns =str
.No specify file type (default Sy  Ns )
.It Sy --histogram-bins Ns =int
.No number of bins for histogram of numeric columns (default Sy 0 Ns )
.It Sy --histogram-even-interval Ns =bool
.No if histogram bins should have even distribution of rows (default Sy False Ns )
.It Sy --pyobj-show-hidden Ns =bool
.No show methods and _private properties (default Sy False Ns )
.It Sy --melt-var-colname Ns =str
.No column name to use for the melted variable name (default Sy Variable Ns )
.It Sy --melt-value-colname Ns =str
.No column name to use for the melted value (default Sy Value Ns )
.It Sy --delay Ns =float
.No --play delay between commands, in seconds (default Sy 0.0 Ns )
.It Sy --regex-maxsplit Ns =int
.No maxsplit to pass to regex.split (default Sy 0 Ns )
.It Sy --csv-dialect Ns =str
.No dialect passed to csv.reader (default Sy excel Ns )
.It Sy --csv-delimiter Ns =str
.No delimiter passed to csv.reader (default Sy , Ns )
.It Sy --csv-quotechar Ns =str
.No quotechar passed to csv.reader (default Sy " Ns )
.It Sy --csv-skipinitialspace Ns =bool
.No skipinitialspace passed to csv.reader (default Sy True Ns )
.It Sy --fixed-rows Ns =int
.No number of rows to check for fixed width columns (default Sy 1000 Ns )
