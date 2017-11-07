# VisiData version history

# next

- rename skiplines option to skip
- rename headerlines option to header
- move Path and subclasses out of vdtui
- TextSheet source is any iterable of strings
- Sheet.filetype provides default save filename extension
- remove default names for unnamed columns
- `Shift-R` now opens a new sheet with # randomly selected rows
- `Shift-P` now pastes above the current row (like vim)
- add threads column and `^C` to SheetsSheet
- Bugfix: Joins
- add `m` and `gm` commands to graph column(s) vs keys
- history up/down in edit widget now feels right
- remove default names for unnamed columns
- add `ga` to add N new rows
- add `gz=` to set selected/all rows to a Python sequence in this column

## 0.97 (2017-10-05)
- Features
    - [replay]
        - move vdplay into vd --play
        - -p --play now replays scripts live
        - --delay interspaces replay by delay seconds
        - --batch to replay without interface
        - --output to save at end of replay
        - --replay-movement=True has --play move the cursor cell-by-cell
        - -y --confirm-overwrite=False
        - replay scripts can be strformatted with field=value
        - add ^U command to pause/resume playback
        - add ^K to cancel replay
        - add Space command to go to next step of replay while paused
    - [global]
        - remap toggle to 't' (was Space)
        - remap ^Y to push sheet of cursorRow
        - 'A' creates new sheet with N empty columns
        - remap 'r' to regex search of row key
        - add zr/zc to go to row/col number
        - F1/z? now launches man page
        - gF1/gz? now launches commands sheet
        - add `f` command to fill empty cells with the content of a non-empty cell up the current column
        - add Del/gDel to set value(s) to None
        - remove TAB/Shift-TAB sheet cycling
        - add z^ command to set current column name to current cell value
        - add gz^ to set current column name to cell values in selected rows
        - add 'z=' to show computed expression over current row
        - z' adds cache to current column (gz' for all columns)
        - `gh` moves cursor to leftmost column (instead of leftmost non-key column)
    - [aggregators]
        - allow multiple aggregators
        - 'g+ adds an aggregator to selected columns on columns sheets
        - sets the exact set of aggregators on the column sheet with 'e'/'ge'
        - 'z+' displays result of aggregation over selected rows for current column on status
        - rework aggregators so multiple aggregators can be set
    - [sheets sheet]
        - '&' on Sheets sheet is now sole join sheet command; jointype is input directly
        - add sheet concat
    - [columns sheet]
        - remap ~!@#$%^ on Columns sheet to behave like they do on other sheets
        - add g prefix to ~!@#$%^ to operate on all 'selected rows' on Columns sheet (thus modifying column parameters on source sheet)
    - [textsheet]
        - add 'w' command on TextSheets to toggle wrap
    - [cmdlog]
        - editlog renamed to cmdlog
        - cmdlog has a new format which minimises recordings of movement commands
        - '^D' now saves cmdlog sheet
    - [pivot]
        - zEnter pushes this cell; Enter pushes whole row
    - [describe]
        - add DescribeSheet with 'I' command for viewing descriptive statistics
        - add zs/zu/zt/zEnter commands to engage with rows on source sheet which are being described in current cell of describe sheet
    - [frequency]
        - 'zF' provides summary aggregation
    - [metasheets]
        - add hidden source column to metasheets
        - ^P view status history
    - [loaders]
        - add 'postgres' schema for simple loader from postgres:// url
        - add gEnter for .zip file mass open
        - add 'fixed' filetype to use fixed column detector
    - [clipboard]
        - remove `B` clipboard sheet
        - rework all d/y/p commands for only one buffer
        - remove g^Z and gp
    - [options]
        - remove -d debug option
        - add --diff to add colorizer against base sheet
            - diffs a pair of tsvs cell-by-cell
        - theme options removed as CLI arguments (still available for .visidatarc or apps)
        - `'` appends frozen column
        - rename and reorder options
- Community
    - [docs]
        - replace .rst userguide with VisiData [man page](http://visidata.org/man)
    - [visidata.org]
        - update index.html
        - automate creation of tour pages from tours.vd
            - tours will be played and recorded using asciinema
            - then compiled into a .html with mkdemo.py for http://visidata.org/tour
        - upload html version of manpage
- Internals
    - renamed toplevel command() to globalCommand(); removed Sheet.command(); sheet commands now specified in Sheet.commands list of Command() objects at class level
    - setter API now (sheet,col,row,value)
    - move `visidata/addons/*.py` into toplevel package

## 0.96 (2017-08-21)
- data can be piped through stdin
- remap: `N` is now previous match (instead of `p`)
- `:` now regex split
- add `bin/viewtsv` example tsv viewer as an example of a small vdtui application
- add `options.cmd_after_edit` for automove after edit
- add clipboard functionality
    - `y` yanks row at cursor to clipboard; `gy` copies all selected rows
    - `d` deletes row and move to clipboard; `gd` moves all selected rows
    - `p` now pastes the row most recently added to the clipboard after current row; `gp` pastes all rows from clipboard after current row
    - `Shift-B` opens clipboard sheet
    - `Ctrl-z` now undoes the most recent delete; `gCtrl-z` undoes all deletes
- Fix cursor row highlighting of identical rows

## v0.95.2
- move some functionality out of vdtui into seperate python files
- add Ctrl-z command to launch external $EDITOR
- add ``options.force_valid_names``

## v0.94 (2017-08-02)
- add options.textwrap for TextSheet
- add vd.remove(sheet)
- Sheet.sources now  modifiable

## v0.93 (2017-07-30)
- fix display/feel bugs in editText
- remove BACKSPACE for editlog undo
- fix colorizer API
- add `ctrl-u` command to toggle profiling of main thread
- fix `C`olumn statistics (`options.col_stats` still disabled by default)

## v0.92 (2017-07-11)
- `F`requency sheet groups numeric data into intervals
   - added `histogram_bins` and `histogram_even_interval` options
   - added `w` command on the sheet that toggles `histogram_even_interval`
- change key for 'eval Python expression as new pyobj sheet' from Ctrl-O to Ctrl-X

## v0.91 (2017-06-28)
- make options automatically typed based on default
- documentation cleanups
- remove R command (set filetype on CLI)

## v0.80
- tour of screenshot.gif
- regex transform now `*` (';' is still regex split)
- Make regex search/select to work more like vim
- Move several non-essential commands out of vd.py
- change license of vd.py to MIT
- vdtutor start
- currency type with `$`; str type moved to `~`; remove type autodetect
- www/ for landing page
- move from .md to .rst for documentation

## v0.61 (2017-06-12)
- colorizers
- `g[` and `g]` to sort by all key columns
- `;` and `.` experimental regex commands

## v0.59 (2017-05-31)
- pivot sheets with `W`
- undo with `BACKSPACE` and replay with `ga`
- dev guide and user guide
- `ge` mass edit
- freeze with `g'`

## v0.44
- creating sustainable dev process at RC
- `z` scrolling prefix

## v0.42
- async select/unselect
- aggregator functions on columns
- .xls

## v0.41 (2017-01-18)
- asynchronous commands (each in its own thread) with
   - `^T` sheet of long-running commands
   - `^C` cancel
   - `ENTER` to see the final performance profile
- `P` random population of current sheet
- headerlines default now 1

## v0.40
- options settable with command-line arguments (`--encoding=cp437`)
- input() histories with UP/DOWN (and viewable with `I`)
- unicode input now works
- editText clears value on first typing
- `"` duplicates sheet with only selected rows; `g"` duplicates entire sheet verbatim

## v0.38
- sortable date
- open_zip comes back

## v0.37
- `g~` (autodetect all columns)
- `"` copies row to immediately following
- nulls, uniques on columns sheet

## v0.36
- right column
- regex subst
- unreverse [/] sort keys ([ = ascending)

## v0.35 (2016-12-04)
- reverse [/] sort keys
- goto `r`ow by number or `c`olumn by name

## v0.33
- type detection with `~`
- date type
- fix outer join

## v0.32
- expose col.type in column header
- push value conversion to time of usage/display

## v0.31
- F1 help sheet
- ^O directly exposes eval result as sheet
- custom editText with initial value, ESC that raises VEscape, and readline edit keys

## v0.30 (2016-11-27)
- make all sheets subclasses of VSheet
- remove .zip opening and url fetching
- added options ColumnStats and csv_header

## v0.29
- pin key columns to left
- join sheets on exact key match
- -r/--readonly mode

## v0.28 (2016-11-22)
- inputs: .csv, .tsv, .json, .hdf5, .xlsx, .zip
- outputs: .csv, .tsv
- hjkl cursor movement, t/m/b scroll to position screen cursor
- skip up/down columns by value
- row/column reordering and deleting
- resize column to fix max width of onscreen row
- filter/search by regex in column
- sort asc/desc by one column
- `g`lobal prefix supersizes many commands
- `e`dit cell contents
- convert column to int/str/float
- reload sheet with different format options
- add new column by Python expression
- `s`elect/`u`nselect rows, bulk delete with `gd`
- `F`requency table for current column with histogram
- `S`heets metasheet to manage/navigate multiple sheets,
- `C`olumns metasheet
- `O`ptions sheet to change the style or behavior
- `E`rror metasheet
- `g^P` status history sheet

## v0.14 (2016-11-13)
