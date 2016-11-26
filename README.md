# VisiData v0.29

A curses interface for exploring and arranging tabular data

Usable via any remote shell which has Python3 installed.

## Features

- inputs: .csv, .tsv, .json, .hdf5, .xlsx
- outputs: .csv, .tsv
- hjkl cursor movement, t/m/b scroll to position screen cursor
- skip up/down columns by value
- row/column reordering and deleting
- resize column to fix max width of onscreen row
- sort asc/desc by one column
- 'g'lobal prefix supersizes many commands
- 'e'dit cell contents
- convert column to int/str/float
- reload sheet with different format options
- add new column by Python expression
- 's'elect/'u'nselect rows, bulk delete with 'gd'
- search/select by regex in column
- 'F'requency table for current column with histogram
- 'S'heets metasheet to manage/navigate multiple sheets,
- 'C'olumns metasheet
- 'O'ptions sheet to change the style or behavior
- 'E'rror metasheet
- 'g^P' status history sheet

## Installation

- Copy the vd.py script to a bin/ directory in PATH and make it executable.
- Install any required dependencies:

### Dependencies

- Python 3.?
- openpyxl (if reading xlsx files)
- h5py (if reading HDF5 files)
- numpy (h5py dependency, and general utility)

## Usage

        $ vd.py [-r/--readonly] [<input> ...]

Inputs may be paths or URLs.  If no inputs are given, starts exploring the
current directory.  Unknown filetypes are by default viewed with a text
browser.

### Working keys

The 'g' prefix indicates 'global' context (e.g. apply action to *all* columns) for the next command only.

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
|   **h**/**j**/**k**/**l** or **\<arrows\>** | Move cell cursor left/down/up/right | Move cursor all the way to the left/bottom/top/right |
| **PgDn**/**PgUp** | Scroll sheet one page down/up (minus stickied rows/columns) |  Go to first/last page |
|   **t**/**m**/**b**   | Scrolls cursor row to top/middle/bottom of screen |
|   **^G**      | Show sheet info on statusline |
|   **^P**      | Show last status message | Open status history |
|   **^R**      | Reload sheet from source |
|   **^S**     | Save current sheet to new file (type based on extension) |
|   **R**      | Change type of sheet (requires ^R reload to reparse) |
|  **Ctrl-^** | Toggle to previous sheet |
|
|    **S**      | View current sheet stack |
|    **C**      | Build column summary |
|
|    **F**      | Build frequency table for current column |
|    **O**      | Show/edit options |
|
|    **E**      | View stack trace for previous exceptions | View stacktraces for last 100 exceptions |
|    **^E**     | Abort and print last exception and stacktrace to terminal |
|    **^D**     | Toggle debug mode (future exceptions abort program) |
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
| Modifying commands (disabled with -r argument or options.readonly=True)
|
|**H**/**J**/**K**/**L** | Move current column or row one to the left/down/up/right (changes data ordering) | "Throw" the column/row all the way to the left/bottom/top/right |
|    **^**      | Set name of current column | Set names of all columns to the values in the current row |
|    **-** (hyphen)   | Delete current column |
| **d**  | Delete current row | Delete all selected rows |
| **#**/**$**/**%** | Convert column to int/string/float |
|  **e** | Edit current cell value |
|  **=** | Add new column by Python expression |
| **.** (period) | Make current column a key (pin to left and match on join) |

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
| ** * ** (asterisk) | Join all selected sheets, keeping all rows from all sheets (full join) |
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

