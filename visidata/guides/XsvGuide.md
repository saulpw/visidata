CSV/TSV options

## `tsv` (Tab Separated Values), as simple as it gets

- {help.options.delimiter}
- {help.options.row_delimiter}
- {help.options.tsv_safe_newline}
- {help.options.tsv_safe_tab}

Use `-f usv` for Unicode separators U+241F and U+241E.
Use `-f lsv` for awk-like records.
Use `--delimiter=` (an empty string) to make '\0' the value separator.
Use `--row-delimiter=` to make '\0' the row separator.

## `csv` (Comma Separated Values) for maximum computibility

.csv files are a scourge upon the earth, and still regrettably common.
All csv_* options are passed unchanged into csv.reader() and csv.writer().

- {help.options.csv_dialect}
   - Accepted dialects are `excel-tab`, `unix`, and `excel`.
- {help.options.csv_delimiter}
- {help.options.csv_quotechar}
- {help.options.csv_skipinitialspace}
- {help.options.csv_escapechar}
- {help.options.csv_lineterminator}

## Saving TSV/CSV files

- {help.options.save_filetype}
- {help.options.safety_first}

## Useful options for text formats in general

- {help.options.regex_skip}
- {help.options.save_encoding}
