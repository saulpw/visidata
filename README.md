# VisiData v0.27

A curses interface for exploring and arranging tabular data

Usable via any remote shell which has Python3 installed.

## Features

- can browse data in .csv, .tsv, .xlsx, .json, .hdf5, .zip formats
- instantly create frequency table for column
- search/select by regex
- meta sheets (columns, options, even the sheets list itself)

## Installation

- Copy the vd.py script to a bin/ directory in PATH and make it executable.
- Install any required dependencies:

### Dependencies

- Python 3.?
- openpyxl (if reading xlsx files)
- h5py (if reading HDF5 files)
- numpy (h5py dependency, and general utility)

## Usage

        $ vd.py <input-file>

where `<input-file>` is a one of the supported file formats.

### Working keys

The 'g' prefix indicates 'global' context (e.g. apply action to *all* columns) for the next command only.

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
|   **h**/**j**/**k**/**l** or **\<arrows\>** | move cell cursor left/down/up/right | move cursor all the way to the left/bottom/top/right |
| **PgDn**/**PgUp** | scroll sheet one page down/up (minus stickied rows/columns) |  go to first/last page |
|   **t**/**m**/**b**   | move cursor to top/middle/bottom row on screen |
|   **^G**      | show sheet info on statusline |
|   **^P**      | show last status message | open status history |
|   **^R**      | reload sheet from source |
|   **^S**     | save current sheet to new file (type based on extension) |
|   **R**      | change type of sheet (requires ^R reload to reparse) |
|
|    **S**      | view current sheet stack |
|    **C**      | build column summary.   shows stats (min/median/mean/max/stddev) |
|
|    **F**      | build frequency table for current column |
|    **O**      | show options |
|
|    **E**      | view stack trace for previous error | quit and print stack trace to terminal |
|    **_**      | Set width of current column to fit values on screen | Set width of all columns to fit values on screen |
|    **^**      | Set name of current column | Set name of all columns to the values in the current row |
|    **[**/**]**    | Sort by current column (asc/desc) |
|   **<**/**>**     | skip up/down to next value in column |
|
|  **/** **?**    | Search forward/backward by regex in current column | search all columns
| **p**/**n**  | Go to previous/next search match | Go to first/last match |
|
|    **\|**     | select by regex if this column matches | select row if any column matches |
|    **\\**     | unselect by regex or expression in this column | unselect row if any column matches | |
|    **\<Space\>/u**  | select/unselect current row | select/unselect all rows |
|
| **d**  | Delete current row |
|**H**/**J**/**K**/**L** (or shift-arrows) | move current column or row one to the left/down/up/right (changes data ordering) | "throw" the column/row all the way to the left/bottom/top/right |
|

### HDF5 sheets

| Keybinding | Action | with 'g' prefix |
| ---: | --- | --- |
|  **<Enter>** | open the group or dataset under the cursor |
|  **A**   | view attributes of currently selected object | view attributes of current sheet |


### Configurable Options (via shift-'O')

| Option | Default value | notes |
| ---: | --- | --- |
| `csv_dialect` | `sniff` | as passed to csv.reader |
| `csv_delimiter` | `\|` |
| `csv_quotechar` | `"` |
|
| `encoding` | `utf-8`| as passed to codecs.open |
| `encoding_errors` | `surrogateescape`|
|
| `VisibleNone` | ``|  visible contents of a cell whose value was None |
| `ColumnFiller` | ` `| pad chars after column value |
| `Ellipsis` | `…`|
| `ColumnSep` | `  `|  chars between columns |
| `SubsheetSep` | `~`|
| `StatusSep` | ` | `|
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

## License

VisiData is licensed under GPLv3.

