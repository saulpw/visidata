# VisiData v0.33

A curses interface for exploring and arranging tabular data

Usable via any remote shell which has Python3 installed.

## Features
- 'F1' for command help sheet
- 'o'pen .csv, .tsv, .json, .hdf5, .xlsx
- 'Ctrl-S'ave .csv, .tsv
- hjkl cursor movement, 't'op/'m'iddle/'b'ottom scroll to position screen cursor
- '['/']' sort asc/desc by one column
- 'e'dit cell contents
- search/select/unselect by regex in column
- 'F'requency table for current column with histogram
- inner/outer/full/diff joins on any number of sheets, matching designated key columns
- add new column by Python expression
- Ctrl-O to eval an expression and browse the result as a python object

### Metasheets

- 'E'rror metasheet
- 'S'heets metasheet to manage/navigate multiple sheets
- 'C'olumns metasheet
- 'O'ptions sheet to change the style or behavior

### Columns

On the 'C'olumns sheet, these commands apply to rows (the columns of the source sheet), instead of the columns on the Columns sheet

- '-' hides column (sets width to 0)
- '\_' maximizes column width to fit longest value
- '!' marks column as a key column (pins to the left and matches on sheet joins)

#### Column typing

- columns start out untyped (unless the source data is typed)
   - '#' sets column type to int
   - '$' sets column type to str
   - '%' sets column type to float
   - '@' sets column type to date
   - '~' autodetects column type
- all values are stored in their original format, and only converted on demand and as needed.
- values that can't be properly converted are flagged with '~' on the display
- for commands like sort which require a correctly typed value, the default (0) value for that type is used
- cell edits are rejected if they don't convert to the column type

## Installation

Copy the vd.py script to a bin/vd directory in PATH and make it executable.

    OR

        $ pip3 install visidata

### Dependencies

- Python 3.?
- openpyxl (if reading .xlsx files)
- h5py and numpy (if reading .hdf5 files)

## Usage

        $ vd [-r/--readonly] [<input> ...]

Inputs may be paths or URLs.  If no inputs are given, starts exploring the
current directory.  Unknown filetypes are by default viewed with a text
browser.

### Working keys

The 'g' prefix indicates 'global' context (e.g. apply action to *all* columns) for the next command only.

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
|   **F1** | Show help screen with list of commands |
|   **h**/**j**/**k**/**l** or **\<arrows\>** | Move cell cursor left/down/up/right | Move cursor all the way to the left/bottom/top/right |
| **PgDn**/**PgUp** | Scroll sheet one page down/up (minus stickied rows/columns) |  Go to first/last page |
|   **t**/**m**/**b**   | Scrolls cursor row to top/middle/bottom of screen |
|   **Ctrl-G**      | Show sheet info on statusline |
|   **Ctrl-P**      | Show last status message | Open status history |
|   **Ctrl-R**      | Reload sheet from source |
|   **Ctrl-S**     | Save current sheet to new file (type based on extension) |
| **o** | open local file or url |
| **Ctrl-O** | eval Python expression and push the result |
|   **R**      | Change type of sheet (requires reload (Ctrl-R) to reparse) |
|  **Ctrl-^** | Toggle to previous sheet |
|
|    **S**      | View current sheet stack |
|    **C**      | Build column summary |
|    **F**      | Build frequency table for current column |
|    **O**      | Show/edit options |
|
|    **E**      | View stack trace for previous exceptions | View stacktraces for last 100 exceptions |
|    **Ctrl-E**     | Abort and print last exception and stacktrace to terminal |
|    **Ctrl-D**     | Toggle debug mode (future exceptions abort program) |
|
|    **_** (underscore)     | Set width of current column to fit values on screen | Set width of all columns to fit values on screen |
|    **[**/**]**    | Sort by current column (asc/desc) |
|   **<**/**>**     | Skip up/down to next value in column |
|
|  **/** / **?**    | Search forward/backward by regex in current column | Search all columns
| **p**/**n**  | Go to previous/next search match | Go to first/last match |
| **\|**//**\\** | Select/Unselect rows by regex if this column matches | Select/Unselect rows if any column matches |
| **s**/**u**/**\<Space\>** | Select/Unselect/Toggle current row | Select/Unselect/Toggle all rows |
|
|**H**/**J**/**K**/**L** | Move current column or row one to the left/down/up/right (changes data ordering) | "Throw" the column/row all the way to the left/bottom/top/right |
|    **^**      | Set name of current column | Set names of all columns to the values in the current row |
|    **-** (hyphen)   | Delete current column |
| **d**  | Delete current row | Delete all selected rows |
| **#**/**$**/**%** | Convert column to int/string/float |
|  **e** | Edit current cell value |
|  **=** | Add new column by Python expression |
| **!** | Make current column a key (pin to left and match on join) |
| **~** | Autodetect this column | Autodetect all columns |

### HDF5 sheets

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
|  **<Enter>** | Open the group or dataset under the cursor |
|  **A**   | View attributes of currently selected object | View attributes of current sheet |

### 'S'heets commands

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
| **&** | Join all selected sheets, keeping only rows which match keys on all sheets (inner join) |
| **+** | Join all selected sheets, keeping all rows from first sheet (outer join) |
| * (asterisk) | Join all selected sheets, keeping all rows from all sheets (full join) |
| **~** | Join all selected sheets, keeping only rows NOT in all sheets (diff join) |


### Notes

- Edits made to a joined sheet will be reflected in the source sheets.



### Configurable Options (via shift-'O')

| Option | Default value | notes |
| ---: | --- | --- |
| `csv_dialect` | `excel` | as passed to csv.reader |
| `csv_delimiter` | `,` |
| `csv_quotechar` | `"` |
|
| `encoding` | `utf-8`| as passed to codecs.open |
| `encoding_errors` | `surrogateescape`|
|
| `VisibleNone` | ``|  visible contents of a cell whose value was None |
| `ColumnFiller` | ` `| pad chars after column value |
| `Ellipsis` | `…`|
| `ColumnSep` | ` \| `|  chars between columns |
| `SubsheetSep` | `~`|
| `StatusSep` | ` \| `|
| `SheetNameFmt` | `%s\| `|  status line prefix |
| `FunctionError` | `¿`|    when computation fails due to exception |
| `HistogramChar` | `*`|
|  color scheme |
| `c_default` | `normal`|
| `c_Header` | `bold`|
| `c_CurHdr` | `reverse`|
| `c_CurRow` | `reverse`|
| `c_CurCol` | `bold`|
| `c_StatusLine` | `bold`|
| `c_SelectedRow` | `green`|

## Contributions

Created by Saul Pwanson `<vd@saul.pw>`.

VisiData is currently under active development (as of Nov 2016).
Please contact me at the email address above if you would like to contribute.

## Inspirations

- [BurntSushi/xsv](https://github.com/BurntSushi/xsv)
- [andmarti1424/sc-im](https://github.com/andmarti1424/sc-im)
- [teapot](https://www.syntax-k.de/projekte/teapot/)
- and, of course, [VisiCalc](http://danbricklin.com/visicalc.htm)

## License

VisiData is licensed under GPLv3.

