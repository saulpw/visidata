# VisiData version history

# v1.3.1 (2018-08-19)

- [http] add `tab-seperated-values` to content_filetypes mapping
- [join] add `extend` join type to use keep all rows and retain **SheetType** from first selected sheet
- `rename-sheet` renames current sheet to input
- [json] add options.json_indent for pretty-printing
- [tsv json txt] add options.save_errors (default True) to include errors when saving
- remove all options.foo_is_null and fix according to 178-nulls.md
- add `z^C` and `gz^C` to cancel threads in current/selected row(s)
- [bugfix] `^R` (reload) on a filtered sheet (`"`) now reloads only the filtered rows
- [aggregators] fix summation with exceptions
- [DirSheet] add `gz^R` (reload-rows) to undo modifications on selected rows

# v1.3 (2018-08-11)

- commands overhaul; see `commands.tsv` (command longnames should now be largely stable)
- add quantile aggregators (q3/q4/q5/q10)
- add `z;` to add new column from bash *expr*, with `$`columnNames as variables
- keyboard layout (thanks to @deinspanjer for the inspiration)
- `O` launches sheet-specific options (see design/169.md); `gO` launches global OptionsSheet
- options.wrap now defaults to False
- options.quitguard enables confirmation before quitting last sheet
- options.safety_first makes loading/saving more robust, at the cost of performance
   - currently only removing NULs from csv input
- dedup, sort, color status messages by "priority" (thanks to @jsvine for suggestion)
- remove menu system
- can now edit source values from FreqSheet

- Command changes
    - `^H` is now main command to open the manpage!  `z^H` opens a list of all commands for this sheet.
    - `R` (`random-sheet`) pushes sheet instead of selecting (reverting to former behavior)
    - `za` (`addcol-empty`) asks for column name
    - `zd` (`delete-cell`) moves value to clipboard ("cut", like other delete commands)
    - add `gI` (`describe-all`) like `gC` (`columns-all`)
    - add `gS` (`sheets-graveyard`)
    - add `g(`, `z(`, `gz(` variants of `(` 'expand-column'
    - add `z|` and `z\` to un/select by python expr (thanks to @jsvine for suggestion)
    - add `z#` to set type of current column to `len`
    - add `z;` to get the stdout/stderr from running a cmdline program with $colname args
    - `Space` is now bound to exec-longname (was `menu`; `^A` was exec-longname previously)

- Loaders:
    - add pandas adapter
    - add xml loader
    - add pcap loader (thanks to @vbrown608 and @TemperedNetworks)
    - add yaml loader (thanks to @robcarrington, @JKiely, @anjakefala at PyCon Sprints for making this happen)
    - add jsonl saver
    - remove `tsv_safe_char` and split into `tsv_safe_newline` and `tsv_safe_tab`

- initial commit of a task warrior app (vtask)

## minor changes
- more portable system clipboard handling (thanks @chocolateboy for PR)
- [json] no more incremental display during loading (need better json parser than stdlib)
- `date` supports adding a number of days (or `6*hours`, `9*months`, etc)
- hidden columns are darkened on columns sheet
- exception rollup
- dev/commands.tsv table of commands
- motd default url uses https
- improve ProfileSheet
- [DirSheet] editable `mode` (set to octal like `0o0644`)

# v1.2.1 (2018-07-05)

- python 3.7
    - Change `async` decorator to `asyncthread` and rename `async.py` to avoid using Python 3.7 keyword

# v1.2 (2018-04-30)

- macro system
   - `gD` goes to directory browser of `options.visidata_dir` (default to `~/.visidata/`) which contains saved commandlogs and macros
   - `z^S` on CommandLog saves selected rows to macro for given keystroke, saving to `.visidata/macro/command-longname.vd`
   - macro list saved at `.visidata/macros.vd` (keystroke, filename)
- `options.cmdlog_histfile` for auto-appended (default: empty means disabled)
- [DirSheet] edits make deferred changes to any field
   - add `directory` and `filetype` columns
   - note: only 256 changes maintained per column (same as column cache size)
   - `^S` saves all deferred changes
   - `z^S` saves changes for the current file only
   - `^R` clears all changes (reload)
   - `z^R` clears changes on the current file only
   - `d`/`gd` marks the current/selected file for deletion
   - if `directory` is edited, on `^S` (save) file is moved (if directory not existing, a new directory is created)
- [New conda package](https://github.com/conda-forge/visidata-feedstock)
- add .visidatarc [snippets](https://github.com/saulpw/visidata/tree/stable/snippets) with examples of extra functionality
- add replayable options [#97](https://github.com/saulpw/visidata/issues/97)
- `g^S` for multisave to single file (`.html`, `.md` and `.txt` are currently supported) or directory
- `z^S` to save selected rows of current column only (along with key columns)
- `T` to transpose rows and columns [#129](https://github.com/saulpw/visidata/issues/129)
- `^A` to specify a command longname to execute
- `^O`/`g^O` to open current/selected files in external editor
- `g^R` on SheetsSheet to reload all [selected] sheets
- `options.error_is_null` to treat errors as nulls when applicable
- `g,` fixed to compare by visible column values, not by row objects
- `gv` to unhide all columns
- `gM` open melted sheet (unpivot) with key columns retained and *regex* capture groups determining how the non-key columns will be reduced to Variable-Value rows
- `g*` replace selected row cells in current column with regex transform
- Shift-Up/Down aliases for mac [#135](https://github.com/saulpw/visidata/issues/135)
- options.wrap now true by default on TextSheet (`v` to toggle)
- `save_txt` with single column concatenates all values to single file
- `+` can add multiple aggregators
- ^X bugfix: use evalexpr over cursorRow
- `z`/`gz` `s`/`t`/`u` to select to/from cursorRow
- `z<` and `z>` to move up/down to next null cell
- `"` no longer reselects all rows
- `sheet-set-diff` command to act like `--diff`
- math functions (like sin/cos) now at toplevel
- bugfix: freeze
- all `csv_` options sent to csv.reader/writer
- `options.tsv_safe_char` to replace \t and \n in tsv files; set to empty for speedup during tsv save
- loaders and savers
    - support bz2 and xz (LZMA) compression (thanks @jpgrayson)
    - add loaders for:
        - sas7bda (SAS; requires `sas7bdat`)
        - xpt (SAS; requires `xport`)
        - sav (SPSS; requires `savReaderWriter`)
        - dta (Stata; requires `pandas`)
    - .shp can save as .geojson
    - add htm as alias for html filetype
    - json bugfix: fix [#133](https://github.com/saulpw/visidata/issues/133) json loader column deduction
- [experimental] bin/vsh initial commit

# v1.1 (2018-03-05)

- VisiData will be included in the [next debian repository release](https://tracker.debian.org/pkg/visidata)!
- remove all install dependencies
  - additional libraries must be installed manually for certain loaders; see requirements.txt
- experimental hierarchical menu system with SPACE to explore commands
    - use standard movement keys (`hjkl`/`arrows`) to navigate within a command level
    - Use `Enter`/`q` to navigate down/up a command tree
    - abort with `gq` or `^C`
    - existing chooseOne selections (aggregators/joins) still use simple input() for now
    - most longnames changed
        - let me know if anyone is using any longnames at all, and we will stabilize the names
    - if you do end up playing with it, please let me know what did and didn't work for you
- randomized message/announcement/tip on startup; disable with `options.motd_url = None`
   - cache messages in `$HOME/.visidata/`

Command additions/changes:

- add `za` and `gza` to add 1/N new blanks column
- add `(` and `)` commands to expand/collapse list/dict columns (e.g. in nested json)
- add `Backspace` command to drop sheet like `q` and also scrub its history from the cmdlog
- [canvas] add `d` and `gd` to delete points from source sheet
- remove `!@#$%-_` special actions on columns sheet
- alias Shift+Arrows to `HJKL` (may not work in all environments)
- alias `ENTER` to modify-edit-cell by default
- add `Y`/`gY`/`zY` to copy row/selected/cell to system clipboard (with options.clipboard_copy_cmd)

- filename `-` works to specify stdin/stdout (`-b -o -` will dump final sheet to stdout)
- search/select uses most recent when not given any (as in vim/etc)
- annotate None with disp_note_none ('∅'); previously was not visually distinguishable from empty string

- save to .md org-mode compatible table format
- load/view/edit/save png, edit pixels in data form
- load/view ttf/otf font files
- [canvas] draw quadratic curves with qcurve([(x,y)...])
- improvements/bugfixes: pivot, describe, melt, sqlite, shp, html

# v1.0 (2018-01-24)

- date.__sub__ returns timedelta object (was int days)
- pivot table bugfixes
- many cosmetic fixes
- disable default profiling for perf improvements
- remove .visidatarc support in PWD or XDG; only $HOME/.visidatarc supported now
- website and docs complete overhaul
- do not execute .py files
- apt/brew packages submitted

# v0.99 (2017-12-22)

- tab completion for filename and python expr
- `v` now 'visibility toggle' (moved from `w`)
- `^W` to erase a word in the line editor
- `gC`
- `--version` (thanks to @jsvine)
- `options.use_default_colors` (thanks to @wavexx)
- `median` aggregator
- .html loads tables (requires lxml)
  - simple http works (requires requests)
- json save
- json incremental load
- [cmdlog] use rowkey if available instead of row number; options.rowkey_prefix
- [cmdlog] only set row/col when relevant
- [vdtui] task renamed to thread
- /howto/dev/loader
- /design/graphics

# v0.98.1 (2017-12-04)

- [packaging]
    - make non Python standard library loader dependencies optional
    - provide method for full installation via `pip3 install "visidata[full]"`
- [visidata.org](http://visidata.org)  change copyright in footer
- [docs] add csv dialects to manpage (closes issue #88)
- [bugfix]
    - fix for `^Z` in builtin line editor
    - fixed-width loader needs source kwarg

# v0.98 (2017-11-23)

- [visidata.org](http://visidata.org) revamp

- [canvas] graphs and maps!
    - `.` or `g.` to push a graph or a map from the current sheet (dot=plot)
    - supports .shp and vector .mbtiles
    - mouse left-click/drag to set cursor
    - mouse right-click/drag to scroll canvas
    - scrollwheel to zoom in/out on a canvas
    - `s`/`u` to select/unselect rows at canvas cursor
    - `ENTER` to push source sheet with only rows at canvas cursor
    - 1-9 to toggle display of 'layers' (colors)
    - `_` to zoom out to full width
    - `disp_pixel_random` option chooses pixel attrs at random (weighted), instead of most common
    - `+`/`-` to zoom in/out via keyboard

- Updates to commands
    - Remove ` (backtick) command
    - Remove most zscroll commands (`zs`/`ze`)
        - `zz` moves cursor to center, uncertain about the future of `zt` due to conflict with `t` for toggle
    - `ga` adds N new rows
    - `gz=` sets value for selected/all rows to a Python sequence in this column
    - `z_` sets column width to given value
    - `z-` cuts column width in half
    - `P` is now "paste before" (like vim); `R` now pushes a random sample
    - `^Z` now sends SIGSTOP; `^O` "opens" the external $EDITOR (from builtin line editor)
    - [ColumnsSheet] Added `~!@#$` commands back, to set type of source columns
    - `w` is becoming a more universal "visibility toggle"
        - [TextSheet] `w` toggles wordwrap
        - [canvas] `w` toggles display of the labels
        - [pyobj] `w` toggles hidden properties and methods

- Updates to command line args and options
    - set initial row/col with `+<row#>:<col#>` (numeric only)
    - `--delimiter`/`-d ` option (separate from `--csv-delimiter`) sets delimiter for tsv filetype
    - `--replay-wait`/`-w` renamed from `--delay`/`-d`
    - `disp_date_fmt` option for date display format string (default is date-only)
    - `zero_is_null`/`empty_is_null`/`none_is_null`/`false_is_null` set which values are considered null (previously was `aggr_null_filter`)
    - `--skiplines` option renamed to `--skip`, and `--headerlines` to `--header`

- Design improvements
    - Add specific rowtype for each sheet (see right status)
    - dates are a kind of numeric type (useful for graphing as the x-axis)
    - `use_default_colors` (at behest of @wavexx)
    - more robust Progress indicator
    - populate DescribeSheet in async thread
    - remove default names for unnamed columns
    - history up/down in edit widget now feels right

- API changes
    - change main Column API to getter(col, row) and setter(col, row, val)
    - move Path and subclasses out of vdtui
    - TextSheet source is any iterable of strings
    - Sheet.filetype provides default save filename extension


## 0.97.1 (2017-10-29)
- Fix postgres lazy import
- BugFix: issue #83 - `z?` works on OSX
- BugFix: <Enter> on SheetsSheets itself now does nothing
- Move from readthedocs to visidata.org


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
