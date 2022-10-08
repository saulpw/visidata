# VisiData version history

# v2.10.2 (2022-10-XX)

- add .vdx, a simplified new cmdlog format
- add `-N`/`--nothing` command to disable loading .visidatarc and plugin addons
- add `addcol-aggr` to add an aggregator column to the **FreqTable** without needing to
  regenerate it (requested by @geekscrapy #1541)

## Improvements

- [cli] load commandline file arguments from the start (requested by @reagle #1471)
- [cli] `--config=''` now does not try to load any config
- [open] rename `zo` `open-cell` command to `open-cell-file`
- [loaders whl] load python .whl (reported by @frosencrantz #1539)

## Bugfixes

- [cli] fix for empty arg
- [DirSheet] fix bug where `Enter` no longer opened a file from the **DirSheet** (reported by @frosencrantz #1527)
- [input paste] fix pasting via a Path via `Ctrl+Y`  into input (reported by @frosencrantz #1546)
- [menu] allow VisiData to run without menu
- [mouse] catch any curses.getmouse() errors (reported by @geekscrapy #1553)
- [performance] allow vd to be truly idle (reported by WizzardUU #1532)
- [plugins_autoload] catch error for environment having invalid package metadata (reported by @jsdealy #1529)
- [plugins_autoload] catch exception if plugin fails to load
- [plugins-autoload] fix check for if plugins_autoload is set in args
- [plugins-autoload] update for importlib-metadata 5.0 API (reported by @jkerhin #1550)
- [pyobj] undo rename of `open-row`/`open-cell` (were renamed to `open-X-pyobj`) (revert of eff9833e6A)
- [sheets] ensure IndexSheets are precious, and that **SheetsSheet** is not (reported by @frosencrantz #1547)
- [unzip-http] extracting a file now checks for overwrite (reported by @frosencrantz #1452)
- [windows clipboard] fix piping to clip command through stdin (thanks @daviewales for the fix; reported by @pshangov #1431)

## API

- expose `CommandLogBase` (was `_CommandLog`)
- [options] allow FooSheet.options instead of .class_options
- add seperate non-async `select_row`, `toggle_row`, and `unselect_row` for selection of single rows
- the before/after decorators now do not fail if api functions they are decorating do not already exist

# v2.10.1 (2022-09-14)

## Improvements

- [docs] document `-d` option (thanks @abitrolly for PR #1515)
- [freq] disable histogram if `disp_histlen` or `disp_histogram` set to 0 or empty string
- [guard] add `guard-sheet-off` which unsets `options.quitguard` on current sheet (thanks @hanfried for PR #1517)
- [menu] add `BUTTON1_CLICKED` (same as `BUTTON1_PRESSED`)
- [open] add `zo` to open file or url from path in current cell

## Bugfixes

- fix Guix build problems (reported by @ryanprior #1499)
- add support for sheet names with multiple `.` (periods) in the name (requested by @geekscrapy #1494)
- [cmdlog] add more portable shebang in vdj
- [date] fix custom date greater than or equal to comparison
- [macros] fix `macro-record` (#1513)
- [macros] refresh `macro-sheet` upon macro addition
- [macros] ensure macros are set upon startup
- [plugins] update usd plugin api (thanks @hanfried for PR #1510)
- [repeat] fix `repeat-` (#1513)
- [status] reduce priority of active colouring (reported by @geekscrapy #804)

## API

- add `ExpandedColumn` to globals
- add `Extensible.before` and `Extensible.after`
  - `def foo` decorated with `@VisiData.before` will run it before `vd.foo()`
  - `def foo` decorated with `@VisiData.after` will run it immediately after



# v2.10 (2022-08-28)

- [plugins] load all entry points in `visidata.plugins` group before config load
  - add entry_points={'visidata.plugins': 'foo=foo'} to plugin load plugin automatically when launching VisiData

- [deps] require `importlib_metadata` >= 3.6
  - following https://github.com/pypa/twine/pull/732

## Improvements

- [draw] redraw only every 100 ms if any keys pending (requested by @ansoncg #1459)
- [IndexSheet] shown name is only final name component
- [loaders html] add table of all links on page (requested by @dufferzafar #1424)
- [loaders html] `open-row` on **LinksSheet** to open url (requested by @dufferzafar #1424)
- [options] add `options.http_req_*` to send headers/etc to requests (requested by @daviewales #1446)
- [options pyobj] add `options.fmt_expand_dict` and `options.fmt_expand_list` for formatting expanded
    list and dict column names (requested by @joe-opensrc #1457)
- [threads-sheet] add `z Ctrl+T` (`threads-sheet`) to open **ThreadsSheet** for current sheet
- [threads-sheet] add `g Ctrl+C` (`cancel-all`) to **ThreadsSheet**
- [zsh] add scripts for zsh completion (PR by @Freed-Wu #1455)
  - tutorial: https://visidata.org/docs/shell/

## Bugfixes

- [addcol-] set cursor at added column for `addcol-new`/`addcol-bulk` (reported by @jsvine #1445)
- [cmdlog] `Ctrl+S` from a **CommandLog** now defaults to `.vdj` (reported by @jsvine #1443)
- [display] format entire string for undetermined width (reported by and fixed by @jsvine #1442)
- [formatter] fix len format strings
- [LastInputsSheet] catch other exceptions during reload
- [loader npz] fix .npz loader (reported by @Shahin-rmz #1440)
- [loader geojson] fix plotting and saving geojson files (fixed by @mwayne #1477)
- [loader geojson] improve feature property manipulation (fixed by @mwayne #1477)
- [menu] upon menu item keypress, move to item (reported by @reagle #1470)
- [menu] fix `ALT+<keystroke>` navigation while within menu (reported by @reagle #1470)
  - now requires two `ESC` to exit
- [open] allow binary files from archives (reported by @frosencrantz #1430)
- [save] do not save unknown filetype as `save_filetype`
- [save visidatarc] only save rows on **OptionsSheet** to visidatarc
- [sheets] fix name reconstruction for files with multiple  and no suffixes (#1450)
- [sheets] do not include empty name parts in sheet name
- [unzip-http] **FreqTableSheet** `open-row` now loads links (reported by @frosencrantz #1458)
- [zip] use correct rowdef in extract (reported by @frosencrantz #1430)
- [zip] do not create directory for extract

## snippets

- add snippets/scrolloff.py which mimics vim's scrollof context lines (requested by @gennaro-tedesco #1441)

## vdplus

- `open-memusage` was moved to vdplus

## API

- add InferColumnsSheet
  - it infers the columns and their types from the rows it gets which are dicts
  - used by json, npy loader
- add vd.printout and vd.printerr for builtins.print to stdout and stderr
- add `vd.view()`
- fix Extensible.init() to work with classes with no `__init__`
- add `Sheet.sidebar` and `Sheet.sidebar_title` properties

## Deprecated

- remove VisiDataSheet
- remove vdmenu

# v2.9.1 (2022-07-21)

- [unzip-http] move urllib3 to optional dependencies

# 2.9 (2022-07-20)

- [ux] add confirming modal dialog
    - only "y" required to confirm
- add XDG support (thanks @jck for the PR #1420)
    - `options.config` default is now `"$XDG_CONFIG_HOME"/visidata/config.py` if `$XDG_CONFIG_HOME` is set and `config.py` exists. If not, falls back to the standard `$HOME/.visidatarc`.
    - vendor [appdirs.py](https://github.com/ActiveState/appdirs/blob/master/appdirs.py)
- [cmdlog] support variables in .vdj (requested by @jungle-boogie #1364)
    - in the .vdj, write variables like so: `${variableName}`
    - then on the CLI: `vd -p foo.vdj variableName=bar`
- [loaders arrow] new Apache Arrow IPC loader/saver (requested by @d-miketa #1369) (requires `pyarrow`)
    - add `.arrow` (file) and .arrows (streaming) formats
    - add more native `parquet` loader via `pyarrow`
- preliminary "windowing" for referencing x rows before and y rows after in an expression (requested by @maxigit #1399, @MMesch #1129, @samuelludwig #1210)
    - press `w` (longname: `addcol-window`) followed by two numbers: the number of rows to aggregate *before* and *after* the current row.
    - there will be a new column, `foo_window`, where each row contains a list of aggregated rows. after that, e.g. `=` `sum(foo_window)` to get a running total for each row
- add `setcol-format-enum` which takes e.g. `A=apple B=banana` and uses that as a mapping when formatting a column.
- vendor `https://github.com/saulpw/unzip-http`; allows the downloading of individual files from a .zip file over http without downloading the entire archive (requires `urllib3` package)
- add `save-source` to save a root sheet directly to its source
- add `setcol-formatter` to specify formatting function used for Column (default: `generic` formats based on type and fmtstr).  Can be `json` or `python` or a custom formatter


## Improvements

- [cli] when `-v` or `-h` VisiData now does not read config or do anything else (requested by @geekscrapy #1340)
- [cmdlog] set `.vdj` to be the default cmdlog format
- [replay] allow column names to be numbers (reported by @frosencrantz #1309)
    - if wishing to reference a column index, required to be an int in a .vdj cmdlog
- [cmdlog] when saving cmdlogs, type column indices as integers, and column names as strings
    - If replaying, and *col* is an `int`, the CmdLog will index by position.
    - If *col* is a `str` it will index by column name.
- [display] preview first n elements of a list/dict cell
- [regex] add unbound `addcol-<regex>` commands
- [rtl] improvements to right-to-left text display (requested by @dotancohen #1392)
- [man] have `vd --help` open the .txt manpage by default (requested by @halloleo #1332)
- [mouse] invert scroll wheel direction (requested by @marcobra #1351)
- [performance] improvements to plotting of empty canvas, multiline display, and draw-ing functions
- [plugins] notify when plugin update available (thanks @geekscrapy for PR #1355)

## Bugfixes

- [aggregators] fail on setting an unknown aggregator in **Columns Sheet** (reported by @geekscrapy #1299)
- [aggregators] handle `delete-cell` case for aggregators column in **Columns Sheet** (reported by @geekscrapy #1299)
- [aggregators] fix quartile aggregators (reported by @pnfnp #1312)
- [aggregators] fix copying of aggregators when duplicating a sheet (reported by @frosencrantz #1373)
- [canvas] do not use "other" label when there are exactly 9 columns being plotted (reported by @tdussa #1198)
- [cli] fix `+:subsheet:col:row:` when `load_lazy` is False
- [delete-row] clear deleted rows from `selectedRows` (reported by @geekscrapy #1284)
- [exec-longname] output warning, if longname does not exist
- [expr] prefer visible columns over hidden columns (reported by @frosencrantz #1360)
- [freeze-sheet] carry over column attributes for freeze-sheet (reported by @frosencrantz #1373)
- [import-python] use command-specific history (reported by @frosencrantz #1243)
- [IndexSheet] fix renaming of sheet names from an IndexSheet (reported by @aborruso #1339)
- [input] handle history for non-string input values (reported by @frosencrantz #1371)
- [loaders pandas] fix (`dup-selected`) `"`of selected rows for **Pandas Sheet** (reported and fixed by @jasonwrith #1315 #1316)
- [loaders usv] swap delimiters (reported by @frosencrantz #1383)
- [loaders usv] save delimiter override options (reported by @frosencrantz #1383)
- [loaders usv] fix saving header with usv row delimiter (reported by @frosencrantz #1383)
- [loaders xlsx] fix clipboard on XlsxSheets (reported by @jungle-boogie #1348)
- [macros] fix macro-record keystroke setting (reported by @fatherofinvention #1280)
- [mouse] stay disabled after input (reported by @holderbp #1401)
- [mouse] fix for pypy3 (thanks @LaPingvino for PR
- [quitguard] refinement of quit-sheet protection (reported by @geekscrapy #1037, #1381)
- [save-selected] get sheet names for saving from selected rows (reported by @aborruso #1339)
- [shell] strip trailing whitespace in `z;` output (reported by @justin2004 #1370)
- [tty] fix bug where piping async output into stdin broke visidata keyboard input (reported by @ovikk13 #1347)
- [undo] fix issue where undoing a reload blanks the current sheet; do not set undos for reload sheet (#1302)
- [unset-option] fix issue where Exception is raised on the next undo-able command run after `unset-option` (reported by @ajkerrigan #1267)
- [windows] require `windows-curses` installation on Windows (thanks @ajkerrigan for PR #1407; reported by @schiltz3 #1268, @aagha #1406)

## API

- add Column.formatter (generic, json, python)
- add SqliteQuerySheet to globals
- `vd.loadConfigFile()` no longer needs a filename argument, and will use `options.config` by default (#211)
- use `newline="` for csv.writer (thanks @daviewales for PR #1368)
- make `ItemColumn` a proper class for inheritance
- add `openJoin` and `openMelt` to allow overriding by plugin sheetsS
- addColumn takes `*cols` (reported by @pyglot #1414)

## Deprecated

- deprecate old vdmenu system
    - remove `Shift+V` command

# 2.8 (2021-12-15)

## Improvements

- [plugins] include pip stderr in warning
- [plugins] use returncode to determine if pip install failed, before adding to imports (thanks @geekscrapy for PR #1215)
- [cmdlog] add sheet creation command to cmdlog (requested by @aborruso #1209)
- [open] strip whitespace from the beginning and end of inputted filenames
- [options] `options.input_history` and `options.cmdlog_histfile` can now be an absolute paths (requested by @geekscrapy #1200)
    - relative paths are relative to `options.visidata_dir`
- [splitwin] automatically switch to pane where sheet is pushed to

## Bugfixes

- [curses] suppress invalid color errors in Python 3.10 (thanks @ajkerrigan for reporting #1227 and for PR #1231)
    - Adapt to [Python 3.10 curses changes](https://docs.python.org/3/whatsnew/3.10.html#curses) which can raise a `ValueError` on invalid color numbers.
- [curses cosmetic] simplify error message, if curses fails to initialise
- [loaders json] skip blank lines in json files, instead of stopping at them (thanks @geekscrapy for PR #1216)
- [loaders jsonl] fix duplicate columns when loading fixed columns sheets in jsonl format (report by @0ceanlight)
    - example of formats with fixed columns is darkdraw's `DrawingSheet`
- [loaders fixed] fix saver (thanks @geekscrapy for PR #1238)
- [loaders postgres] fix recognition of postgres loader (reported by @ryanmjacobs #1229)
- [loaders sqlite] fix the loading of sqlite VIEWs for sqlite version 3.36.0+ (reported by @frosencrantz #1222)
- [help-commands] now lists commands only for the current sheet (reported by @geekscrapy #1217)
- [textcanvas] ENTER on canvas should push copied source sheet for points within cursor
- [pivot freq] use `options.histogram_bins` from source sheet
- [curses cosmetic] fix issue where if a curses initialisation Exception is called, a second Exception follows
- [quit-sheet-free] fix bug where quit-sheet-free, when multiple sheets opened in CLI, was not working (reported by @geekscrapy #1236)
- [options] fix instance where local options sheet was called, instead of global options sheet (thanks @geekscrapy for PR #1241)

## API

- add standard Python `breakpoint()` to drop into the pdb debugger
- export `run()` to global api
- add CsvSheet, ZipSheet, TarSheet to global api (thanks @geekscrapy for PR #1235)

# 2.7.1 (2021-11-15)

- Bugfix: fix Enter on helpmenu (reported by @geekscrapy #1196)

# 2.7 (2021-11-14)

## Improvements

- [movement] bind Home/End to go-top/go-bottom (thanks @geekscrapy #1161)
- [api] add vd.urlcache as alias for urlcache global (thanks @geekscrapy for PR #1164)
- [plugins] do not continue installation if main package fails pip install (thanks @geekscrapy for PR #1194)
- [plugins] allow for plugin records without SHA256; warn if absent (thanks @geekscrapy for PR #1183)
- [load_lazy] do not load subsheets, if `sheet.options.load_lazy` is True (thanks @geekscrapy for PR #1193)
- [save] confirm when `save_foo` function does not exist and saver fallsback to `options.save_filetype` (reported by @geekscrapy #1180)
- [save] `options.save_filetype` default now 'tsv'
- several cosmetic improvements

## Loaders

- [lsv] add `lsv` filetype for simple awk-like records (requested by @fourjay #1179)
- [ods] add `odf` filetype for Open Document Format spreadsheets
- [xlsx] add extra columns (`cellobject`, `fontcolor`, `fillcolor`) if `options.xlsx_meta_columns` (default False) (thanks @hoclun-rigsep for PR #1098)
- [sqlite] allow query/insert (no modify/delete yet) for `WITHOUT ROWID` tables (requested by @stephancb #1111)

## Bugfixes

- [savers compression formats] fix corruption when saving to compression formats (#1159)
- fix "ModuleNotFoundError: no module named 'plugins'" error on startup (#1131 #1152)
- [windows] fix issue with Enter key on Windows (reported by @hossam-houssien #1154)
- [draw] fix multiline rows by making height fixed for all rows (reported by @geekscrapy #916)
- [DirSheet] fix bug where fix key column sheets (e.g. DirSheet, SqliteIndexSheet) keycols were not being saved in batchmode (reported by @geekscrapy #1181)
- [async] make sure all threads started on sheet are cancelable (reported by @geekscrapy #1136)
- [AttrDict] fix bug with setting value on nested AttrDict
- [dup-X-deep] fix error with async_deepcopy (thanks @pstuifzand for fix)
- [join] fix 'inconsistent-keys' issue when joining between XlsxSheet with typed columns and CsvSheet with untyped columns (reported by @davidwales #1124)
- [sqlite] handle sqlite column names with spaces (thanks @davidskeck for PR #1157)
- [sqlite] use `options.encoding` and `options.encoding_errors` for decoding of sqlite db text (reported by @WesleyAC #1156)
- [xlsx] add handling for EmptyCell instances (thanks @hoclun-rigsep for PR #1121)
- [xlsx] gate sheet name cleaning on `options.clean_names` (reported by @davidwales #1122)
- [macos] fix bindings for `Option`+key
- [random-rows] fix import (reported by @geekscrapy #1162)
- [save-selected] better default save filename (reported by @geekscrapy #1180)
- [save] fix bug where saving multiple sheets to a single non-embeddable format did not result in fail (reported by @geekscrapy #1180)
- [slide] fix Shift slide-down and Shift slide-up with arrow keys (reported by @a-y-u-s-h #1137)
- [replay] fix replay where `join-sheets` operation hangs (reported by @agjohnson #1141)
- [undo] no more KeyError when Undoing modifications (reported by @geekscrapy #1133)
- [unfurl-col] fix unfurl-col on cells containing exceptions (reported by @jsvine #1171)

# 2.6.1 (2021-09-28)

## Bugfixes

- [editor] fix sysopen-row (thanks @frosencrantz #1116)
- [loaders fixed] fix saver (#1123)
- [loaders shell] fix copy-files
- [loaders sqlite] fix import error on exception (thanks @jsvine #1125)

# 2.6 (2021-09-19)

## Major feature

- [menu] new hierarchical menu system
    - `Alt+F`, `Alt+E`, etc to open submenus (`Alt+` underlined capital letter in toplevel menu)
    - `Ctrl+H` to activate Help menu (manpage now at `gCtrl+H`)
    - `q` or `Esc` to exit menu
    - Enter to expand submenu item or execute command
    - or left mouse click to activate and navigate menu
    - only show commands available on current sheet
    - sheet-specific commands highlighted with `options.color_menu_spec`
    - new options:
      - `disp_menu`: display menu if inactive (default True).  Can still activate menu with Ctrl+H/Alt+F
      - `disp_menu_keys`: whether to display shortcuts inline (default True)
      - `disp_menu_fmt`: upper right display on menu bar (like `disp_status_fmt`/`disp_rstatus_fmt`)
      - theme colors: `color_menu` `color_menu_active` `color_menu_spec` `color_menu_help`
      - theme chars: `disp_menu_boxchars` `disp_menu_more` `disp_menu_push` `disp_menu_input` `disp_menu_fmt`

## Interface changes

- [expand-col] only expand to one level
- [slide] remove slide row/col with mouse
- [macos] add bindings for Option+key to Alt+key
- [modified] limit use of sheet protection (thanks @geekscrapy #1037)
- [python] rebind g^X to new import-python command (what exec-python was mostly used for)
- [npy] add `npy_allow_pickle` option (default False)
- [join] rename join-sheets on IndexSheet to join-selected; bind both g& and & to join-selected
- [loaders pandas] add error message for unpickling non-dataframes
- [join] fail if no key columns on any sheet (thanks @geekscrapy #1061)
- [loaders xlsx] enable access to cell metadata (thanks @hoclun-rigsep #1088)
- many performance, progress bar, and UI responsiveness improvements

## Bugfixes

- [cli] issue warning if +sheet-position not found (thanks @geekscrapy #1046)
- [clipboard] do not copy newline for syscopy-cell (thanks @geekscrapy #1064)
- [column] detect existing column by row key instead of column name (thanks @geekscrapy #1058)
- [color] set `color_current_row` to the same precedence as `color_current_column` (thanks @frosenrantz #1100)
- [command] do not fail/abort on unknown command
- [draw] Sort indicator on top of More indicator (thanks @geekscrapy #1071)
- [join] fix multiple extend (thanks @cwarden)
- [join] allow extended columns to be modified (thanks @cwarden)
- [join] fix for rowdefs without bool (like pandas)
- [loaders dirsheet] continue after exception in copyfile
- [loaders fixed] fix fixed-format saver
- [loaders fixed] save uses `global options.encoding` (thanks @geekscrapy #1060)
- [loaders mysql] do not stop loading on first error (thanks @SuRaMoN #1085)
- [loaders pandas] fix column rename
- [loaders sqlite] save based on column names, not position
- [loaders sqlite] allow changing value of cells that were NULL (thanks @mattenklicker #1052)
- [loaders sqlite] add message on not currently supporting WITHOUT ROWID (thanks @stephancb #1111)
- [multisave] fix breaking typo
- [open_txt] load new blank sheet for 0 byte files (thanks @geekscrapy #1047)
- [save] do not set a default for `options.save_filetype` (thanks @frosencrantz #1072)
- [split-pane mouse] activate pane on click (thanks @frosencrantz #954)
- [unfurl] handle unfurling exceptions (close #1053)
- [quitguard] confirm quit when set on a specific sheet even if not precious or modified
- [yaml] Fix yaml loader traces on no attribute `_colnames` (thanks @frosencrantz #1104)
- [visidatarc] catch all visidatarc exceptions upon load

# v2.5 (2021-07-08)

- [social] #visidata has moved off of freenode to libera.chat
- [deps] required pandas version for the pandas loader has been bumped to at least 1.0.5
- [caa] new PR submitters required to sign CAA

## Features

- [cli] when no arguments on commandline, open currentDirSheet (previously vdmenu); -f opens empty sheet of that filetype
- [clipboard] bind `x` family to `cut-*` (thanks @geekscrapy #895)
- [date] add specialized comparators for `datetime.date` (thanks @aborruso #975)
    - visidata.date now compares to datetime.date (previously raised exception)
        - identical dates compare equal even if intra-day times are different
        - this does not work for incompletely specified visidata.date; e.g.
            `visidata.date(2016, 10, 29, 4, 0, 0) != visidata.date(2016, 10, 29)`
- [DirSheet] add y/gy to copy file(s) to given directory
- [loaders vds] save non-jsonable cells as string (thanks @pacien #1011)
- [loaders zstd] support loading zstd-compressed files (thanks @lxcode #971)
- [movement] bind `Ctrl+Left/Right` to `go-left`/`right-page` (thanks @davidwales #1002)
- [options] save to foo.visidatarc from OptionsSheet (thanks @njthomas #958)
- [sqlite] RENAME and DROP tables from SqliteIndexSheet
- [unfurl] add `options.unfurl_empty` to include row for empty list/dict (thanks @frosencrantz #898)
- [quitguard] confirm quit/reload only if sheet modified (references #955, #844, #483; thanks @jvns, @frosencrantz)

## Improvements

- [addRow] advance cursor if row inserted before cursor
- [archive] add .lzma as alias for .xz
- [clipboard] gzp pastes None if nothing on clipboard
- [clipboard] make syspaste async
- [clipboard] bind `zP` to syspaste-cells and gzP to syspaste-cells-selected (thanks @jvns and frosencrantz #983, #990)
- [cliptext] better support for combining and variant chars (thanks @lxcode #758 #1034)
- [colors] reduce color swatch size to remove flashing (thanks @frosencrantz #946)
- [encoding] specify encoding explicitly for all Path.open_text (thanks @pacien #1016)
- [error] exceptionCaught(status=False) to add to status history, but not post to status (thanks @frosencrantz #982)
- [freqtbl] copy fmtstr from source col to aggcol (thanks @geekscrapy #1003)
- [help] ENTER/exec-command to execute command on undersheet (thanks @geekscrapy #1011)
- [help] add `all_bindings` hidden column (thanks @frosencrantz #896)
- [inputs] put reused input at end of lastInputs (thanks @geekscrapy #1033)
- [loaders json] streamify save to .json
- [loaders npy] add `npy_allow_pickle` option, default False
- [loaders tsv] increase bufsize to improve loader performance by 10%
- [path] all Path.open track Progress via read/filesize (thanks @jspatz #987)
- [path] add Progress for opening compressed files
- [path] implement line-seek operations (thanks @pacien #1010)
- [regex expand] deprecate `options.expand_col_scanrows`; standardize on `options.default_sample_size` (thanks @jsvine)
- [regex] "match regex" to "capture regex" (thanks @geekscrapy #1032)
- [shell] `addcol-shell` pass command to $SHELL (thanks @juston2004 #1023)
- [shortcut] allow shortcut for jump-sheet to be settable
- [splitwin] push sheet in empty pane iff splitwin
- [stdin] use cli --encoding option for piped data (thanks @pacien #1018)
- [undo] remove undo for reload (replaced with quitguard+confirm)
- [quit] add Shift+Q/quit-sheet-free to quit and free associated memory (thanks @cwarden)

## Display
- [canvas] add `options.disp_canvas_charset` to change displayed chars (thanks @albert-ying #963)
- [canvas] use sheet specific options for draw
- [disp] format list/dict as [n]/{n} only for anytype
- [save] iterdispvals(format=True) convert None to empty string

## Bugfixes

- [batch] ensure quitguard is off during batch mode
- [canvas[ fix error on dive into cursor including y-axis
- [cli] have an actual error if there is a missing argument for final option
- [cli] do nothing (no error) if no sources given
- [clipboard] fix zy/gzp regression (thanks @sfranky #961)
- [clipboard] syscopy-cell do not include column name
- [cmdlog] fix bug where customising replayable options in Options Sheet led to issues opening metasheets (thanks @jsvine #952)
- [cmdlog] fix bug where cmdlog records new sheet name, instead of old sheet name for `rename-sheet` (thanks @aborruso #979)
- [color] track precedence so colorizers apply over `color_current_row`
- [color] determine color availability with `init_pair`
- [color] do not break on nonsense color
- [column] getitemdeep/setitemdeep get/set dotted item key if exists (thanks @frosencrantz #991)
- [column] fix bug where hard crash occurs when cursor on cell of SheetsSheet is on cursorDisplay (thanks @frosencrantz #1029)
- [curses] add default `vd.tstp_signal` for non-cli users
- [execCommand] warn gracefully if bound command longname does not exist
- [expr] setValuesFromExpr do not stop processing on exception
- [join] fix when keys have different names (thanks @aborruso #964)
- [join] fix for rowdefs without bool (like pandas)
- [join] fix multiple extend (thanks @cwarden for reporting)
- [loaders fixed] fix editing in final column for fixed-width load (thanks @mwayne #974)
- [loaders geojson] do not abort plot if rows have errors
- [loaders html] add columns even if not in first row
- [loaders pandas] fix column rename
- [loaders rec json] fix adding new columns for json and rec loaders (thanks @ajkerrigan #959)
- [loaders postgresql] add postgresql scheme (fixes #966) (thanks @zormit #967)
- [loaders sqlite] fix saving deleted cells (thanks @mattenklicker #969)
- [loaders vds] save SettableColumn as Column (thanks @pacien #1012)
- [loaders zip] fix extract-selected-to
- [open] fix regression where opening blank sheets of type tsv, csv, txt, etc was not working
- [plugins] fix stdout/error from plugins installation message (was in bytes, changed to str)
- [quit] remove sheets from **Sheets Sheet** upon quit
- [save-col] fix inputPath error (thanks @savulchik #962)
- [shell] fix `options.dir_hidden`; also apply to dirs when `dir_recurse`
- [textsheet] fix reload after `^O` sysopen

## vdplus

- moved clickhouse, vsh, vgit, windows to vdplus


# v2.4 (2021-04-11)

- [splitwindow] stabilize sheet stack associations
    - `Shift+Z` pushes 'under sheet' (if any) onto other stack
    - `Shift+Z` does not swap panes anymore
    - `g Tab` swaps panes
    - `options.disp_splitwin_pct` is always not sheet-specific

- [status] show nSelectedRows on rstatus

- [color] remove `options.use_default_colors` (thanks @lxcode #939)
    - `options.color_default` can now have both fg and bg
    - other color options which do not specify fg or bg will use the missing component from `color_default`
    - to use terminal default colors, set `options.color_default=""`

## Bugfixes

- [loaders gzip] fix progress bar when opening gzip (thanks @geekscrapy #925)
- [loaders http] fix loading files from url without specifying filetype
- [loaders sqlite] use `TABLE_XINFO` for hidden/virtual columns (thanks @dotcs #945)
- [loaders sqlite] perf improvement: do not pre-count rows (required full table scan)
- [loaders vds] save typed values instead of formatted display values (thanks @frosencrantz #885)
- [loaders xlsx] stringify "header" row values for column names (thanks @davidwales #921)
- [pyobj-show-hidden] grab visibility lvl from sheet specific option (thanks @frosencrantz #947)
- [splitwin] prevent flickering-on-full-window
- [splitwin] if top sheet quit, keep bottom sheet in bottom pane
- [splitwin] full-screen/splitwin close all sheets should be part of the same stack

# v2.3 (2021-04-03)

## Features
    - [colors] allow background colors (thanks @frosencrantz #435)
        - use "*fg* on *bg*" e.g. "212 yellow on 14 red"
            - "bg *bg* fg *fg*" (or reversed)
            - attributes always apply to foreground regardless of position in colorstr
            - as before, only the first valid color in a category (fg/bg) is used; subsequent color names (even unknown ones) are ignored
        - allocate colors on demand, instead of "all" 256 colors as fg
        - **Colors Sheet** now only includes colors actually allocated
    - [colors] set `use_default_colors` default to `True` (was `False`)
    - [delete] do not move deleted values to clipboard (thanks @geekscrapy #895)
        - `delete-*` commands are changed to not alter the clipboard
        - the previous `delete-*` commands are renamed to `cut-*` (unbound)
        - this affects: `delete-row`, `delete-selected`, `delete-cell`, `delete-cells`
    - [jump-first] bound `g^^` to cycle through sheets
    - [null] `zd` / `gzd` `delete-cells` set to `options.null_value` instead of `None`
    - [memories] add MemorySheet on `Alt+M`, `Alt+m` adds current cell to sheet  (thanks @UrDub and @geekscrapy #912)
        - useful for storing values to reference later
        - both names and values can be edited on MemorySheet
        - [aggregator] `memo-aggregator`(z+; formerly called `show-aggregate`) adds value to memory sheet
        - [clipboard] clipboard stored on memory sheet; zy/zp use vd.memory.clipval;
    - [plugins] allow install from github url to local pip repo
    - [plugins] add darkdraw to plugins.jsonl
    - [png] save image as RGBA
    - [pyobj-expr] `Ctrl+X` within `Ctrl+X` input suspends directly into python REPL
    - [splitwin] now involves two different sheetstacks that build and quit independently (thanks @lamchau #894)
        - [splitwin] allows stickier panes for push/quit
    - [splitwin] splitwin-half (`Z`) swaps panes if already active
    - [splitwin] only re-split (with `zZ`) if sheets are not already split, otherwise adjust split percent
    - [save_filetype] if `save_ext` does not exist, or if `options.save_filetype` is different from default, use `options.save_filetype`
    - [vdplus] auto-import, ignore if not available

## Bugfixes
    - [aggregator] fix typo in deciles description (thanks @cwarden #922)
    - [copy] copying BasicRow (new sheets), now does not error (still blank)
    - [cmdlog] for `open-file` source logging in cmdlog, we want paths to physical files, so if src is a **Sheet** grabs its source
    - [defer] fix pasting in deferred sheets
    - [eval] fix **ExprColumns** on empty rows
    - [help] move signal config earlier in runcycle, to accomodate --help (thanks @frosencrantz #926)
    - [open] create blank sheet of appropriate type when path does not exist
    - [pandas] fix conflict between dropped index and existing column (thanks thomanq #937)
    - [plugins] only check for plugins.jsonl once daily (previously: every start-up)
    - [pivot] fix `openRow`
    - [pivot] fix bug with sheet name
    - [png] fix saving directly from canvas
    - [sort] fix sorting of visidata.Path objects (thanks @frosencrantz #897)
    - [splitwin] fix cursor behaviour on both panes when active
        - cursor movement on inactive panes is blocked
    - [SuspendCurses] workaround for bug in curses.wrapper (thanks @frosencrantz #899)
    - [undo] do not set undo for a `commit-sheet`

## Api
    - [addRows] addRows(rows, index, undo) adds rows at index, sets undo if True
        - set undo to False, if using addRows within an addUndo function
    - [deleteBy] add an undo flag to deleteBy
    - [clipboard] change `cliprows` to be a simple list of rows
    - new **DrawablePane** super-base class
    - [json] rowdef now **AttrDict** for massive convenience

# v2.2.1 (2021-02-07)

## Bugfixes
    - [setcol-fill] use row identity to identify selected rows (thanks @frosencrantz, #884)
        - for jsonl, empty rows are identical ({}), and if ones is selected, previously it would result in all of them being filled.
        - also, fill with most recent *non-null* value

## man
    - add a manpage visidata.1
    - fix typo

# v2.2 (2021-01-30)

## Options

    - [cli options] now global by default; use `-n` to set option as sheet-specific instead
        - add `-n`/`--nonglobal` to make subsequent CLI options "sheet-specific" (applying only to paths specified directly on the CLI)
        - keep `-g`/`--global` to make subsequent CLI options "global" (applying to all sheets by default unless overriden)
        - invert the default: now CLI options are global by default (thus `-g` is a no-op unless preceded by `-n` on the CLI)
        - `-g` no longer acts as a toggle

    - [input] add `options.input_history` (thanks @tsibley and @ajkerrigan #468)
        - basename of file to store persistent input history (default of `''` means disabled)
        - caveat: persistent file only read if option given before first input

    - [options.fancy_chooser] now disabled by default--use `Ctrl+X` to open from a choose() prompt

## Types

    - [types] add `floatlocale` type (thanks @Guiriguanche #863)
        - add commands `type-floatlocale` and `type-floatlocale-selected` (unbound by default)
        - `floatlocale` parses based on `LC_NUMERIC` envvar (must be set before launching)
        - parsing is 20x slower than with standard float column
        - will parse commas as decimals (e.g. '1,1') if LC_NUMERIC is set to a locale like 'en_DK.UTF-8'

## Loaders

    - [loaders geojson] add loading and saving support for geojson files (thanks @draco #876)
    - [loaders vds] add loader/saver for custom .vds format (VisiData Sheet) to save column properties and data for multiple sheets in one file
    - [ux] autoload all subsheets by default; set `options.load_lazy` to disable
        - removes a minor friction with unloaded subsheets

    - [loaders http] add `options.http_max_next` to limit api pagination (default 0 - no pagination) (thanks @aborruso #830)

## Bugfixes and Adjustments

    - [cli] fail properly if path cannot be opened
    - [defer] only mention number of deleted rows, if some were deleted
    - [go-pageup go-pagedown] ensure cursor stays in the same relative positions
    - [loaders mysql] fix mysql loader duplicating tables for each database (thanks @SuRaMoN #868)
    - [loaders mysql] perform asynchronous data fetch for mysql loader (thanks @SuRaMoN #869)
    - [loaders pandas] fix empty subsets for dup-selected and frequency table `open-row` (thanks @ajkerrigan #881 #878)
    - [loaders shp] fix display (thanks @dracos #874)
    - [loaders shp] fix saving to geojson (thanks @dracos #876)
    - [replay] fix replaying of .vd with `set-option`
    - [slide] fix bug when sliding key columns to the left, after sliding them to the right
    - [types] add command `type-floatsi-selected` on **Columns Sheet**

    - [expand] errors and nulls can now be expanded with `expand-cols` (thanks @geekscrapy #865)

    - [open] openSource now uses **'global'** `options.filetype` instead of sheet-specific as previous
        - to set the filetype for a file locally, set through cli: `vd -f tsv sample.foo`
        - to set in the **CommandLog**, use sheet="global" with longname="set-option"

    - [loaders http] raise exception if http status is not 20x (thanks @geekscrapy #848)
    - [loaders shp] support more Shapefile types (thanks @dracos #875)

## API
    - add `create` kwarg to `openSource()`, to create the file if it does not exist already
    - [settings] 'global' is now 'default', and 'override' is 'global'
        - 'default' is the default setting within VisiData
        - 'global' is a user override on that default that applies globally
        - sheet-specific overrides global and default, for the sheet it is specific to
        - options set through visidatarc and cli are 'global' unless otherwise specified
    - [save] grab `save_foo` from **SheetType** first
        - allows overrides of sheet-specific saving

# v2.1.1 (2021-01-03)

    - [macros] allow macro interfaces to be longnames (thanks @frosencrantz #787)
    - [save] better default save filename for url sheets (thanks @geekscrapy #824)

## Bugfixes
    - [cmdlog] record column, sheet, and row info for open-cell
    - [cmdlog] catch case of 'override' sheet for set-option
    - [expr-col] `curcol` now works for multiple invocations (thanks @geekscrapy #659)
    - [loaders postgres] account for postgres_schema when rendering Postgres tables (thanks @jdormit for PR #852)
    - [loaders url] fail unknown URL scheme (thanks @geekscrapy for PR #84)
    - [pyobj] fix Pyobj Sheets for lists (thanks @brookskindle #843)
    - [pipe] handle broken pipes gracefully (thanks @robdmc #851)
    - [scroll] fix issue with jagged scrolling down (thanks @uoee #832)
    - [sort] fix bug where total progress in sorting is (100 * # of columns to sort) (thanks @cwarden)

## api
    - format_field formats int(0) and float(0.0) as "0" (thanks @geekscrapy for PR #821)
    - add TypedWrapper.__len__ (thanks @geekscrapy)

# v2.1 (2020-12-06)

    - [add] add bulk rows and cols leave cursor on first added (like add singles)
    - [add] add colname input to `addcol-new`
    - [aggregators] add mode and stdev to aggregator options (thanks @jsvine for PR #754)
    - [api] add options.unset()
    - [columns] add hidden 'keycol' to **ColumnsSheet**  (thanks @geekscrapy for feature request #768)
    - [cli] support running as `python -m visidata` (thanks @abitrolly for PR #785)
    - [cli] add `#!vd -p` as first line of `.vdj` for executable vd script
    - [cli] allow `=` in `.vd` replay parameters
    - [clipboard] clipboard commands now require some selected rows #681
    - [commands] add unset-option command bound to `d` on OptionsSheet #733
    - [config] `--config=''` now ignores visidatarc (thanks @rswgnu for feature request #777)
    - [defer] commit changes, even if no deferred changes
    - [deprecated] add traceback warnings for deprecated calls (thanks @ajkerrigan for PR #724)
    - [display] add sort indication #582
    - [display] show ellipsis on left side with non-zero hoffset (thanks @frosencrantz for feature request #751)
    - [expr] allow column attributes as variables (thanks @frosencrantz for feature request #659)
    - [freq] change `numeric_binning` back to False by default
    - [input] Shift+Arrow within `edit-cell` to move cursor and re-enter edit mode
    - [loaders http] have automatic API pagination (thanks @geekscrapy for feature request #480)
    - [loaders json] improve loading speedup 50% (thanks @lxcode for investigating and pointing this out #765)
        - this makes JSON saving non-deterministic in Python 3.6, as the order of fields output is dependent on the order within the dict
            - (this is the default behaviour for dicts in Python 3.7+)
    - [loaders json] try loading as jsonl before json (inverted)
        - jsonl is a streamable format, so this way it doesn't have to wait for the entire contents to be loaded before failing to parse as json and then trying to parse as jsonl
        - fixes api loading with http so that contents of each response are added as they happen
        - unfurl toplevel lists
        - functionally now jsonl and json are identical
    - [loaders json] try parsing `options.json_indent` as int (thanks @frosencrantz for the bug report #753)
         this means json output can't be indented with a number. this seems like an uncommon use case
    - [loaders json] skip lines starting with `#`
    - [loaders pdf] `options.pdf_tables` to parse tables from pdf with tabular
    - [loaders sqlite] use rowid to update and delete rows
        - note that this will not work with WITHOUT ROWID sqlite tables
    - [loaders xlsx] add active column (thanks @kbd for feature request #726)
    - [loaders zip] add extract-file, extract-selected, extract-file-to, extract-selected-to commands
    - [macros] add improved macro system (thanks @bob-u for feature request #755)
        - `m` (`macro-record`) begins recording macro; `m` prompts for keystroke, and completes recording
        - macro can then be executed everytime provided keystroke is used, will override existing keybinding
        - `gm` opens an index of all existing macros, can be directly viewed with `Enter` and then modified with `Ctrl+S`
        - macros will run command on current row, column sheet
        - remove deprecated `z Ctrl+D` older iteration of macro system
    - [regex] use capture names for column names, if available, in `capture-col` (thanks @tsibley for PR #808)
        - allows for pre-determining friendlier column names, saving a renaming step later
    - [save] `g Ctrl+S` is `save-sheets-selected` on **IndexSheet**
        - new command allows some or all sheets on an **IndexSheet** to be saved (and not the sheets on the sheet stack)
    - [saver] add fixed-width saver (uses col.width)
    - [saver sqlite] ensureLoaded when saving sheets to sqlite db
    - [search] `search-next` and `searchr-next` are now bound to n and N (was `next-search` and `search-prev`)
    - [select] differentiate select-equal- and select-exact- (thanks @geekscrapy for feature request #734)
       - previous select-equal- matched type value
       - now select-equal- matches display value
       - add `z,` and `gz,` bindings for select-exact-cell/-row
    - [sheets] sorting on **SheetsSheet** now does not sort **SheetsSheet** itself. (thanks @klartext and @geekscrapy for bug reports #761 #518)
    - [status] use `color_working` for progress indicator (thanks @geekscrapy for feature request #804)
    - [types] add floatsi parser (sponsored feature by @anjakefala #661)
        - floatsi type now parses SI strings (like 2.3M)
        - use `z%` to set column type to floatsi

## Bugfixes

    - [api] expose visidata.view (thanks @alekibango for bug report #732)
    - [color] use `color_column_sep` for sep chars (thanks @geekscrapy for bug report)
    - [defer] frozen columns should not be deferred (thanks @frosencrantz for bug report #786)
    - [dir] fix commit-sheet and delete-row on DirSheet
    - [draw] fix display for off-screen cursor with multiline rows
    - [expr] remove duplicate tabbing suggestions (thanks @geekscrapy for bug report #747)
    - [expr] never include computing column (thanks @geekscrapy for bug report #756)
        - only checks for self-reference; 2+ cycles still raises RecursionException
        - caches are now for each cell, instead of for each row
    - [freeze] freeze-sheet with errors should replace with null
    - [loaders frictionless] assume JSON if no format (thanks scls19fr for bug report #803)
        - from https://specs.frictionlessdata.io/data-resource/#data-location):
            - a consumer of resource object MAY assume if no format or mediatype property is provided that the data is JSON and attempt to process it as such.

    - [loaders hdf5] misc bugfixes to hdf5 dataset loading (thanks @amotl for PR #728)
    - [loaders jsonl] fix copy-rows
    - [loaders pandas] support loading Python objects directly (thanks @ajkerrigan for PR #816 and scls19fr for bug report #798)
    - [loaders pandas] ensure all column names are strings (thanks @ajkerrigan for PR #816 and scls19fr for bug report #800)
    - [loaders pandas] build frequency table using a copy of the source (thanks @ajkerrigan for PR #816 and scls19fr for bug report #802)
    - [loaders sqlite] fix commit-sheet
    - [loaders sqlite] fix commit deletes
    - [loaders xlsx] only reload Workbook sheets to avoid error (thanks @aborruso for bug report #797)
    - [loaders vdj] fix add-row
    - [man] fix warnings with manpage (thanks @jsvine for the bug report #718)
    - [movement] fix scroll-cells (thanks @jsvine for bug report #762)
    - [numeric binning] perform degenerate binning when number of bins greater than number of values
        - (instead of when greater than width of bins)
    -  [numeric binning] if width of bins is 1, fallback to degenerate binning
    - [numeric binning] degenerate binning should resemble non-numeric binning (thanks @setop for bug report #791)
    - [options] fix `confirm_overwrite` in batch mode
        - fix `-y` to set `confirm_overwrite` to False (means, no confirmation necessary for overwrite)
        - make `confirm()` always fail in batch mode
        - make `confirm_overwrite` a sheet-specific option
    - [plugins] only reload **Plugins Sheet** if not already loaded
    - [replay] move to replay context after getting sheet (thanks @rswgnu for bug report #796)
    - [replay] do not push replaying .vd on sheet stack (thanks @rswgnu for bug report #795)
    - [scroll] zj/zk do nothing in single-line mode (thanks @jsvine for suggestion)
    - [shell] empty stdin to avoid hanging process (thanks @frosencrantz for bug report #752)
    - [status] handle missing attributes in `disp_rstatus_fmt` (thanks @geekscrapy for bug report #764)
    - [tabulate] fix savers to save in their own format (thanks @frosencrantz for bug report #723)
    - [typing] fix indefinite hang for typing (thanks @lxcode for issue #794)
    - [windows] add Ctrl+M as alias for Ctrl+J #741 (thanks @bob-u for bug report #741)
    - [windows man] package man/vd.txt as a fallback for when man is not available on os (thanks @bob-u for bug report #745)

## Plugins
- add conll loader to **PluginsSheet** (thanks @polm)
- remove livesearch
- add clickhouse loader

## Commands
- if `options.some_selected_rows` is True, `setcol-expr`, `setcol-iter`, `setcol-subst`, `setcol-subst`, `setcol-subst-all` will return all rows, if none selected

## API
- [columns] add Column.visibleWidth
- [open] additionally search for `open_filetype` within the vd scope
- [select] rename `someSelectedRows` to `onlySelectedRows`
- [select] add new `someSelectedRows` and `options.some_selected_rows` (thanks maufdez for feature request #767)
    - if options is True, and no rows are selected, `someSelectedRows` will return all rows
- [status] allow non-hashable status msgs by deduping based on stringified contents
- [isNumeric] isNumeric is part of vdobj

# v2.0.1 (2020-10-13)

## Bugfixes
    - Fix printing of motd to status

# v2.0 (2020-10-12)

## Additions and Improvements
    - [aggregators] allow custom aggregators in plugins/visidatarc (thanks @geekscrapy for the feature request #651)
    - [loaders xlsx] automatically clean sheet name when saving; warn if sheet name changes (thanks @geekscrapy for the request #594)
    - [columns] unhide height attribute by default (thanks @frosencrantz for feature request #660)
    - add .vcf (VCard) loader
    - [sqlite] remove name of db from an **SqliteSheet**'s name, only tablename
    - [syspaste] make `syspaste-` replayable and undoable (note that `syspaste-` value will be recorded in **CommandLog**)
    - [savers] many text saver filetypes via tabulate library (thanks @jsvine for original vdtabulate plugin)
    - [calc] ExprColumn no longer cached by default
    - [loaders rec] add new .rec file loader and multisheet saver (recutils)
    - [savers] implemented multisheet saver for both json and jsonl
    - [loaders eml] add new .eml file loader for email files with attachments

## Options
    - add `options.incr_base` (thanks @chocolateboy for the suggestion #647)
    - (former) `options.force_valid_colnames` renamed to `options.clean_names`
        - applies to **Sheets** and **Columns** now (thanks @geekscrapy for the request #594)
    - for --X=Y, do not replace - with _ in Y (thanks @forensicdave for bug report #657)
    - add `options.default_height` for visibility toggle (thanks @frosencrantz for feature request #660)
    - add support for `--` option-ending option on CLI.
    - [input] default now `fancy_chooser` = True
        - when fancy_chooser enabled, aggregators and jointype are chosen with a ChoiceSheet.
        - `s` to select, `Enter` to choose current row, `g Enter` to choose selected rows, `q` to not choose any
    - numeric_binning is now True by default (enables numeric binning on **PivotSheet** and **FreqTable** for numeric columns

## Command changes and additions
        - (former) setcol-range (`gz=`) renamed to `setcol-iter`
        - (former) `addcol-range-step` (`i`) renamed to `addcol-incr-step`
        - (former) `setcol-range` (`gi`) renamed to `setcol-incr`
        - (former) `addcol-range-step` (`zi`) renamed to `addcol-incr-step`
        - (former) `setcol-range-step` (`gzi`) renamed to `setcol-incr-step`
        - add `scroll-cells-*` to scroll display of cells while remaining in a Column; bind to [g]z{hjkl}
        - (former) unbind z{hjkl} from `scroll-col` (thanks @geekscrapy for feature request #662)
        - add `type-floatsi` bound to `z%` (#661)
        - `reload-selected` now reloads all **Sheets** if none selected (thanks @geekscrapy for PR #685)
        - add customdate with fixed fmtstr for parsing (use `z@` and input a fmtstr compatible with strptime (thanks @suntzuisafterU for feature request #677)

## Bugfixes
    - [DirSheet] use changed ext as filetype when loading files (thanks @frosencrantz for bug report #645)
    - [slide] several major improvements to column sliding; key column sliding now works (thanks much to @geekscrapy for bug hunting #640)
    - [open-row] **Sheets Sheet** should be removed from stack upon `open-row` (thanks @cwarden for the bug report)
    - [cli] re-add --version (thanks @mlawren for bug report #674)
    - [open-config] fix `gO` (thanks @geekscrapy for bug report #676)
    - [splitwin] handle swap case for single sheet (thanks @geekscrapy for bug report #679)
    - [loaders xlsx] handle `None` column names for all **Sequence Sheet** loaders (thanks @jsvine for bug report #680)
    - [settings] retrieve from cache for top sheet if obj is None (thanks @aborruso for the bug report #675)
    - [settings] check if option is set on specific sheet before falling back to override
    - [describe] have **DescribeSheet** use source column's sheet's `options.null_value` to calculate its null column (thanks @aborruso for the bug report #675)
    - [undo] ensure that undos for complex commands (like `expand-cols`) are set more frequently (thanks @frosencrantz for the bug report #668)
        - it is still possible to find race conditions if the user presses commands fast enough, however they should happen far less frequently
    - [vlen] fix numeric binning for `vlen()` (thanks @frosencrantz for bug report #690)
    - [pivot] fix pivot case where no aggregator is set
    - [pyobj] fix filtering for **PyobjSheet**
    - [DirSheet] fix sorting for directory column of **DirSheet** (thanks @frosencrantz for bug report #691)
    - [json] fix bug saving cells with nested date values (thanks @ajkerrigan for PR #709)
    - [input] fix Ctrl+W bug when erasing word at beginning of line
    - [plugins] import `.visidata/plugins` by default
    - [pandas] use a safer `reset_index()` to avoid losing data when updating a pandas index (thanks @ajkerrigan for PR #710)
    - [threads] disable `add-row` on **ThreadsSheet** (thanks @geekscrapy for bug report #713)

## deprecated
    - complete removal of `status` and `statuses` from deprecated (thanks @frosencrantz for bug report #621)
        - longnames are now `open-status` and `show-status`
    - remove `cursorColIndex`

## API and Interface
    - `Sheet(*names, **kwargs)` autojoins list of name parts
    - `openSource()`, `aggregator()`, and `aggregators` are now part of vdobj
    - `set_option` is now `setOption`
    - move `isError` to `Column.isError`
    - deprecate `load_pyobj`, now **PyobjSheet**
    - add `.getall('foo_')` which returns all options prefixed with `'foo_'`; deprecated `options('foo_')`
    - `nSelected` is now `nSelectedRows`
    - make `Column.width` property, so setting is same as `Column.setWidth`
    - `evalexpr` is now `evalExpr`
    - `format` is now `formatValue`
    - `SettableColumn.cache` is now `._store`
    - `vdtype()` is now `vd.addType()`
    - add `addColumnAtCursor` (thanks @geekscrapy for bug report #714)

## Plugins
    - update sparkline (thanks @layertwo #696)
    - plugin dependencies now install into `plugins-deps` (former plugin-deps)

## Dev niceties
    - Fully automate dev setup with Gitpod.io (thanks @ajkerrigan for PR #673)


# v2.-4 (2020-07-27)

## Additions and Improvements
    - [cmdlog] allow sheet-specific set-option for replay
    - [columns] add default uppercase names for created columns (like VisiCalc)
        - these names are global; no default name is ever reused
    - [cosmetic] a column with a width 1 will now display (thanks @frosencrantz for the bug report #512)
    - [defer] move defermods and vls back into vdcore
        - configure sqlite and DirSheet to use it
    - [dir] allow explicit filetype when loading a directory (thanks @geekscrapy for the bug report #546)
    - [errors] ErrorsSheet on `g Ctrl+E` lists errors, instead of concatenating
    - [expand-cols] account for all visible rows when expanding a column (thanks @ajkerrigan for PR #497)
    - [loaders csv] use `options.safe_error` for cell exceptions on save
    - [loaders http] use file format in path if loader available (thanks @jsvine for PR #576 and bug report #531)
        - if not, fail back to MIME type (prev behaviour)
    - [loaders imap] add loader for imap://
    - [loaders json] handle non-dict rows in json data (thanks @ajkerrigan for PR #541 and @jsvine for bug report #529)
    - [loaders jsonl] show parse errors in every column
    - [loaders MySQL] add support for MySQL loader (thanks @p3k for PR #617)
    - [loaders pandas] upgrade pandas to 1.0.3 (thanks @ajkerrigan for PR #563)
    - [loaders pandas] add auto-loaders for feather, gbq, orc, parquet, pickle, sas, stata (thanks @khughitt for bug report #460)
    - [loaders pdf] add simple pdf loader
    - [loaders postgres] add support for connecting directly to rds (thanks @danielcynerio for PR #536)
        - the url has the following format: `rds://db_user@hostname:port/region/dbname`
        - it assumes that the AWS IAM for the user is configured properly
    - [loaders xls/xlsx] add save_xls and save_xlsx (thanks @geekscrapy for PR #574)
    - [loaders yaml] allow diving into YAML rows (thanks @ajkerrigan for PR #533)
    - [loaders yaml] use the default safe YAML loader (thanks @tsibley for the PR #600 )
        - the full loader is unsafe because serialized files can be constructed which run arbitrary code during their deserialization
        - the safe loader supports a very large subset of YAML and supports the most common uses of YAML
    - [loaders yaml] support files containing multiple documents (thanks @tsibley for PR #601)
    - [options] set visidata_dir and config from `$VD_DIR` and `$VD_CONFIG` (thanks @tsibley for bug report #448)
    - [type fmtstr] thousands separator (thanks @dimonf for bug report #575)
        - default for int/float is string.format for roundtripping accurately in data text files like csv
        - if fmtstr starts with '%', use locale.format_string (with grouping)
        - otherwise, use python string.format
        - currency uses locale, and is grouped.
    - [quitguard] if set on specific sheet, only confirm quit on that sheet (thanks @jsvine for bug report #538)
    - [undo] add undo for `rename-col-x` family, mouse slide, and `reload-sheet` (thanks @jsvine for feature request #528)

## Command changes
    - [add-sheet] renamed to open-new; new sheet always has a single column
    - [config] bind `g Shift+O` back to open-config (#553)
    - [dive] convert many dive- commands to open- (#557)
        - add open-row bound to `ENTER` on Sheet itself
        - add `open-source` unbound on BaseSheet
        - deprecate `dive-*` longname
    - [options] options-global now `Shift+O`; options-sheet now `z Shift+O`
    - [multi-line] have visibility toggle Multi-Line Row on TextSheets (Closes #513)
        - used to toggle `wrap`

## Command additions
    - [canvas] add resize-x/y-input commands to set x/y axis dimensions (thanks @pigmonkey for feature request #403)
    - [errors] add select-error-col and select-error (thanks @pigmonkey for feature request #402)
    - [input] `Ctrl+Y` paste from cell clipboard
    - [input] Ctrl+Left/Right move cursor to prev/next word
    - [iota] add `i` family of commands (iota/increment)
        - (former) setcol-range (`gz=`) renamed to `setcol-iter`
        - `addcol-range-step` (`i`): add column with incremental value
        - `secol-range` (`gi`): set current column for selected rows to incremental values
        - `addcol-range-step` (`zi`): add column with incremental values times given step
        - `setcol-range` (`gzi`): set current column for selected rows to incremental values times given step
    - [mouse] add unbound `mouse-enable` and `mouse-disable` commands
    - [quitguard add unbound `guard-sheet` command to set quitguard on current sheet (thanks jsvine for feature request #538)
    - [unfurl-col] add command, bound to `zM`, which does row-wise expansion of iterables in a column (thanks @frosencrantz for feature request and jsvine for initial code sample #623)
        - thanks @jsvine for name and initial implementation

## Options
    - [cli] custom cli option parsing (thanks @tsibley for the behaviour request #573)
        - `--options` apply as sheet-specific option overrides to the sources following them
        - the last setting for a given option is the cli-given override setting (applies to all cli sources, unless they have the option already set)
        - this allows both
            - `vd -f csv foo.txt`
            - `vd foo.txt -f csv`
        - `--help` opens the manpage
        - `-g` prefix sets option globally for all sheets
    - [cli] add --imports (default "plugins") (thanks @tsibley for feature request #448)
        - space-separated list of modules to import into globals before loading .visidatarc
        - plugins can be installed by VisiData without modifying .visidatarc
    - [chooser] experimental `options.fancy_chooser`
        - when fancy_chooser enabled, aggregators and jointype are chosen with a ChoiceSheet.
        - press `ENTER` on any row to choose a single option, or select some rows, and press `ENTER` to choose the selectedrows
        - warning: the mechanism to do this effectively launches another instance of visidata, and so it is possible to get into an embedded state (if you jump around sheets, for example, instead of selecting). 'gq' should still work (thought `CTRL+Q` may need to be pressed several times).
    - [dir] add `-r` alias for `--dir-recurse`
    - [join-cols] add `options.value_joiner` to combine cell values for join-col (thanks @aborruso for feature request #550)
    - [join-cols] add `options.name_joiner` to combine column names for join-col, and sheet names for dive-row (thanks @aborruso for feature request #550)
        - sheet names for join-sheets are still joined with '+' or '&' for the time being
    - [loaders html] add `options.html_title` to exclude the sheetname when saving sheet as html table (thanks @geekscrapy for PR #566)
    - [loaders postgres] add support for custom postgres schema (Thanks @p3k for PR #615)
        - schema defaults to `public` but can be overriden using the `--postgres-schema` flag:
        - `vd --postgres-schema=foo postgres://user:pw@localhost/foobar`
    - [loaders zip] -f filetype now applies to inner files
    - [mouse] add options.mouse_interval to control the max time between press/release for click (ms)
        - set to 0 to disable completely
    - [pyobj] add `options.expand_col_scanrows` to set the number of rows to check when expanding columns (0 = all)
    - [type fmtstr] add fmtstr options for numerical types
        - add options.disp_currency_fmt
        - add options.disp_int_fmt
        - add options.disp_date_fmt

## Plugins
    - [dependencies] install plugin dependencies into vd dir (thanks @tsibley for feature request #448)
    - [diff] diff is now a plugin
        - `--diff` is not available as a cmdline argument anymore
    - [vds3] bumped to 0.4 (@ajkerrigan)
    - [marks] initial release 0.1; marks selected rows with a keystroke; utils for selecting + viewing marked rows (@saulpw)
    - [genericSQL] initial release (1.0); basic loader for MySQL (Oracle, MySQL) (@aswanson)
    - [diff] is now a plugin (@saulpw)

## Bugfixes
    - [cmdlog] fix case where CommandLog `open-` entries would not be replayable
    - [cmdlog] record keystrokes for command
    - [cmdlog] global cmdlog behaviour is now consistent with VisiData v1.5.2 cmdlog
    - [dirsheet] check if directory before grabbing filetype from ext (thanks @frosencrantz for bug report #629)
        - handles case where `.` in directory name
    - [helpsheet] do not include deprecated longnames (thanks @frosencrantz for bug report #621)
    - [input] flush input buffer upon newline in input; prevent pastes with accidental newlines from becoming keystrokes (thanks @geekscrapy for bug report #585)
    - [loaders csv] PEP 479 fix for csv loader (thanks @ajkerrigan for PR #499)
        - This avoids the following error when opening CSV files in Python 3.8: `RuntimeError: generator raised StopIteration`, but maintains the behaviour of gracefully handling malformed CSV files.
        - References:
            - https://www.python.org/dev/peps/pep-0479/#examples-of-breakage
            - https://github.com/python/cpython/pull/6381/files
    - [loaders html] cast to str before writing (thanks @geekscrapy for bug report #501)
    - [loaders html md] preserve formatting of display values when saving
    - [loaders html] fix string formatting issue for the html table name when saving (thanks @geekscrapy for PR #566)
    - [loaders pandas] bugfixes for sort (thanks @ajkerrigan for PR #496)
    - [loaders pandas] fix row deletion + its undo (thanks @ajkerrigan for PR #496)
    - [loaders pandas] improve regex select/unselect logic (thanks @ajkerrigan for PR #496)
    - [loaders pandas] fix row selection/deselection (thanks @ajkerrigan for PR #496)
    - [loaders postgres] load an estimate of row numbers for improved performance (thanks @danielcynerio for PR #549)
    - [loaders postgres] fix expand column to work on a json column in postgres (thanks @danielcynerio for PR #552)
    - [loaders sqlite] save display value if not supported sqlite type (thanks @jtf621 for bug report #570)
    - [loaders xml] correctly copy columns; fix path (#504)
    - [numeric-binning] fix numeric-binning bug with currency type column
    - [dir] fix dup-rows-deep on DirSheet (thanks @geekscrapy for bug report #489)
    - [rstatus] fix rstatus when repeating a command with no keystrokes (Thanks @ajkerrigan for bug report #577)
    - [save-sheets] fix saving multi-sheets as individual files to directory
    - [settings] remove internal option defaults from cmdlog
    - [sheets_all] make opened .vd/.vdj precious
    - [transpose] handle case where columns are numeric (thanks @frosencrantz for bug report #631)
    - [undo] fix undo with duplicate-named sheets (thanks @jsvine for bug report #527)
    - [utils] Fix namedlist bug with column named after VisiData attrs (particularly 'length') (thanks @tsibley for bug report #543)
 

## Infrastructure / API
    - [asyncsingle] ensure that unfinished threads decorated with @asyncsingle do not block upon sync()
        - used so that domotd() and PluginsSheet().reload() do not block replay progression
    - [open-] switch from vd.filetype to open_ext; deprecate vd.filetype
    - [warnings] output Python warnings to status

# v2.-3 (2020-03-09)

## Major changes
    - [cosmetic] change default column separators
    - [json] make json load/save key order same as column order (ensures round-trip #429)
    - [commands.tsv] remove commands.tsv; move helpstr into code

## Major features
    - add Split Window
        - options.disp_splitwin_pct (default: 0) controls height of second sheet on screen
    - add .vdj for cmdlog in jsonl format
    - add plugins/bazaar.jsonl for PluginsSheet in jsonl format

### new commands
    - `splitwin-half` (`Shift+Z`)    -- split screen, show sheet under top sheet
    - `splitwin-close` (`g Shift+Z`) -- closes split screen, current sheet full screens
    - `splitwin-swap` (`TAB`)        -- swap to other pane
    - `splitwin-input` (`z Shift+Z`) -- queries for height of split window
    - `repeat-last`  (unbound)       -- run the previous cmd longname with any previous input (thanks #visidata for feature request! #441)
    - `repeat-input` (unbound)       -- run the last command longname with empty, queried input (thanks #visidata for feature request! #441)
    - `resize-cols-input` (`gz_`)    -- resize all visible columns to given input width
        - thanks @sfranky for feature request #414
    - `save-col-keys` (unbound)      -- save current column and key columns
        - fixes #415; thanks @sfranky for feature request

### new options
    - options.disp_float_fmt; default fmtstr to format for float values (default: %0.2f)
        - thanks khughitt for PR! #410

## Additions and Improvements
    - add merge jointype (thanks @sfranky for feature request #405)
        - like "outer" join, except combines columns by name and each cell returns the first non-null/non-error value
        - use color_diff to merge join diffs
        - on edit, set values on *all* sheets which have the given row
    - adjust `save-cmdlog` input message for clarity
    - all sheets have a name (thanks @ajkerrigan for helping iron out the kinks with PR #472)
    - add args re-parsing to handle plugin options (helps with #443; thanks tkossak for bug report)
    - vdmenu should only get pushed outside of replay and batch mode
    - move cursor to row/col of undone command (thanks @jsvine for request)
    - move urlcache into async reload (affects PluginsSheet and motd)
    - add 'type' column to `SheetsSheet`

### Command changes

- `HOME`/`END` now bound to `go-leftmost`/`go-rightmost`
    - thanks [@gerard_sanroma](https://twitter.com/gerard_sanroma/status/1222128370567327746) for request
- `z Ctrl+HOME`/`z Ctrl+END` now bound to `go-top`/`go-bottom`
- `Ctrl+N` now bound to `replay-advance`

### longname renamings
- `search-next` (was `next-search`)
- `search-prev` (was `prev-search`)
- `jump-prev` (was `prev-sheet`)
- `go-prev-value` (was `prev-value`)
- `go-next-value` (was `next-value`)
- `go-prev-selected` (was `prev-selected`)
- `go-next-selected` (was `next-selected`)
- `go-prev-null` (was `prev-null`)
- `go-next-null` (was `next-null`)
- `go-right-page` (was `page-right`)
- `go-left-page` (was `page-left`)

## Plugins
    - add usd plugin
        - provide USD(s) function to convert strings with currencies to equivalent US$ as float
        - uses data from fixer.io
    - add vds3 by @ajkerrigan
        - initial support for browsing S3 paths and read-only access to object
    - add "provides" column for plugins (helps with #449; thanks @tsibley for feature request)
    - standardize author in bazaar.jsonl
        - "Firstname Lastname @githbhandle"

## Bugfixes
    - [cmdlog] fix issue with `append_tsv_row`, that occurred with `options.cmdlog_histfile` set
    - [replay] fix replaying of rowkeys
    - [replay] fix race condition which required the `--replay-wait` workaround
    - [plugins] ensure that `options.confirm_overwrite` applies to plugin installation
    - [slide] fix slide-leftmost
        - had inconsistent behaviour when a sheet had key columns
    - [slide] use visibleCol variants, such that slide works as expected with hidden cols
    - [options min_memory_mb] disable (set to 0) if "free" command not available
    - [core] auto-add raw default column only if options.debug (fixes #424; thanks @frosencrantz for bug report)
    - [cli] fix --config (thanks @osunderdog for bug report! #427)
    - [draw] fix status flickering that occurred with certain terminals (thanks @vapniks for bug report #412)
    - [txt save] save all visibleCols instead of only first one
    - [json] avoid adding columns twice when loading JSON dicts (thanks @ajkerrigan for bug report (#444) and PR (#447)
    - [fixed] fixed error that occurs when there are no headerlines (thanks @frosencrantz for bug report #439)
    - [pcap] update loader with modern api
    - [csv] catch rows with csv.Errors and yield error msg
    - [curses] keypad(1) needs to be set on all newwin (fixes #458)
    - [save-sheets] address two bugs with `g Ctrl+S`
    - [batch api] override editline() in batch mode (addresses #464; thanks @Geoffrey42 for bug report)
    - [replay] better handling of failed confirm (addresses #464; thanks @Geoffrey42 for bug report)
    - [asyncthread] with changed decorators, asyncthread should be the closest decorator to the function
        - if it is not, the act of decorating becomes spawned off, instead of calls to the function being decorated
    - [canvas] update Canvas delete- commands with current API (fixes #334)

## Infrastructure / API
    - rename `Sheet` to `TableSheet`
        - deprecate `Sheet` but keep it around as a synonym probably forever
    - use HTTPS protocol for git submodules (thanks @tombh for PR #419)
        - this allows installation of VisiData in automated environments such as
        Dockerfiles where the git user is not logged into Github
    - unit tests have been migrated to pytest
    - use counter to keep track of frequency of column names
        - for joins, we want un-ambiguous sheets of origin when more than one sheet has a c.name
    - all sheets use addColumn api instead of manually appending columns
    - set terminal height/width via LINES/COLUMNS via curses.use_env (thanks halloleo for feature request #372)
    - update pip command to pull development branch of vsh (thanks @khughitt for PR #457)
    - change longnames *-replay to replay-*
    - rename vd.run() to vd.mainloop()
    - `vd.save_foo(p, *sheets)` throughout
    - standardize on vd.exceptionCaught
    - Sheet.addRows renamed to Sheet.addNewRows
    - option overrides can be done with SubSheet.options
    - options set with Sheet.options
    - extend status() varargs to error/fail/warning
    - add @BaseSheet.command decorator
    - rename tidydata.py to melt.py
    - deprecate globalCommand; use BaseSheet.addCommand
    - remove vd.addCommand
    - deprecate theme(); use option() instead
    - deprecate global bindkey/unbindkey
    - move commands, bindkeys, `_options` globals to vd object
    - DisplayWrapper compares with its value
        - this allows sensible colorizers like `lambda s,c,r,v: v==3`
    - Sheet.addColorizer now apply to single sheet itself (fixes #433; thanks @frosencrantz for bug report)
    - add Sheet.removeColorizer (thanks @frosencrantz for feature request #434)

# v2.-2 (2019-12-03)

## Major changes
    - [cmdlog] every sheet now has its own cmdlog
        - change `Shift+D` to `cmdlog-sheet`, with commands from source sheets recursively
        - `gShift+D` now `cmdlog-all`
        - `zShift+D` `cmdlog-sheet-only`
    - [dirsheet] VisiData's DirSheet is readonly; move write-mode for DirSheet to `vls` (see plugins)
    - [options] `options-global` bound to `gO`and `options-sheet` to `O`
        - `open-config` is now unbound (previously `gO`)
    - [defermods] has been moved to an opt-in plugin
    - [vdmenu] launching `vd` without a source file, opens menu of core sheets
        - press `Enter` to open sheet described in current row

## Major Features
    - [IndexSheet] index into sub-sheets from command line (thanks @aborruso for suggestion #214)
        - currently works for html and hdf5 loaders
        - `+:subsheet:col:row` in cli 
            - `subsheet` the topsheet upon load, with cursor located in cell at `row` and `col`
        - `+:subsheet::` to ignore row/col
        - can name toplevel source index if more than one: `+toplevel:subsheet::`

## Additions and improvements
    - [add-rows] now undo-able
    - [aggregators] show-aggregate with quantiles (thanks @wesleyac for feature request #395)
    - [cli] `-P <longname>` on commandline executes command <longname> on startup 
    - [cmdlog] jump commands are not logged
    - [config] set VisiData height/width via LINES/COLUMNS envvars (thanks @halloleo for suggestion #372)
    - [csv] add `csv_lineterminator` option (default: '\r\n') (thanks @dbandstra for bug report #387)
        - retain csv writer default DOS line endings
    - [describe] add `options.describe_aggrs` (thanks @unhammer for suggestion #273)
        - space-separated list of statistics to calculate for numeric columns
        - default to existing 'mean stdev'
        - add this to .visidatarc for e.g. a harmonic mean to be added automatically to the describe sheet:
            ```
            from statistics import harmonic_mean
            options.describe_aggrs += ' harmonic_mean' # note the leading space
            ```
    - [describe] add hidden "type" col (thanks aborruso for suggestion #356)
    - [dirsheet] add `open-dir-current` command to open the DirSheet for the current directory
    - [help] add `help-commands-all` on `gz^H` (thanks @frosencrantz for suggestion #393)
    - [help] add `help-search` command (thanks @paulklemm for suggestion #247)
        - opens a commands sheet filtered by the input regex.
    - [loaders] add --header and --skip universal handling to all sheets that inherit from `SequenceSheet` (currently tsv/csv/fixed/xlsx/xls)
    - [menu] if no arguments, open VisiData Main Menu instead of DirSheet
    - [plugins] update PluginsSheet to add sha256 and vdpluginsdeps 
    - [plugins] PluginsSheet now loads plugins in `~/.visidata/plugins/__init__.py` instead of in `~/.visidatarc`
        - to use this feature, add `from plugins import *` to `~/.visidatarc`
    - [pyobj] for security reasons, `.py` loader moved out of VisiData core and into snippets
        - Note that the PyObj loader auto-imports `.py` modules upon loading them
    - [ttf] use `Enter` to plot instead of `.`

## Plugins
    - add hello world minimal plugin
    - update viewtsv example (thanks @suhrig for --skip improvement suggestions #347)
    - add vmailcap with `^V` to view by mimetype (thanks @cwarden for suggestion)
    - add basic frictionless loader (thanks @aborruso for suggestion #237)
        - `-f frictionless` with .json either http[s] or local file
        - .zip may not work yet
    - add fdir filetype; opens a DirSheet for a .txt with a list of paths
    - move trackmod and defermod out of VisiData core and into module defermods.py
        - defermods defers saving to source until commit-sheet
            - deleted rows are colored red and visible until commit
        - trackmods tracks changes in source sheet until save-sheet
            - deletes are removed upon delete-row(s)
        - defermods and trackmods are not on by default, `import visidata.defermods` must be added to visidatarc
        - plugin/loader authors: by default, all sheets that inherit from BaseSheet have .defermods=False and .trackmods set to True when defermods is imported
    - create package `vsh`; add to it `vls`, `vping`, `vtop`
        - `vls` contains write-mode for DirSheet
    - add vmutagen for audio tags on DirSheet
        - `Alt+m` to add the mutagen columns on the DirSheet
    - add geocoding using nettoolkit.com API
        - add `addcol-geocode` command to add lat/long columns from location/address column
    - new commands in rownum plugin
        - `addcol-rownum` adds column with original row ordering
        - `addcol-delta` adds column with delta of current column
    - vtask is now a discrete plugin

## Bugfixes
    - [bindkey] move global bindkey after BaseSheet bindkey (thanks @sfranky for bug report #379)
    - [cmdlog] now will check for `confirm-overwrite`
    - [dirsheet] commit/restat/filesize interactions (thanks @Mikee-3000 for bug report #340)
    - [dirsheet] pass filetype to openSource
        - if filetype is not passed, options.filetype would overload file ext
    - [expr] catch recursive expression columns (columns that calculate their cells using themselves) (thanks @chocolateboy for bug report #350)
    - [fixed] various improvements to fixed-width sheet loader (thanks @frosencrantz for thorough bughunting #331)
    - [http] use options.encoding when no encoding is provided by responses headers (thanks @tsibley for the PR #370)
    - [join] joining columns in the ColumnSheet resulted in exception (thanks @frosencrantz for bug report #336)
    - [load] fix replay sync bug (required wait prevously)
        - however, look out for `vd *` with lots of big datasets, they will now all load simultaneously
    - [longname] fix getCommand() error reporting
    - [mbtiles] now works again
    - [metasheets] created VisiDataMetaSheet which sets system TsvSheet options
        - now changes in tsv options for source files will not affect HelpSheet, CmdLog or PluginsSheet
        - thanks frosencrantz for bug report #323
    - [options] no error on unset if option not already set
    - [path] filesize of url is 0
    - [path] fix piping bug (vd failed to read stdin) (thanks @ajkerrigan for bug report #354)
    - [plugins] ensure consisten Python exe for plugin installs (thanks @ajkerrigan for fix)
    - [plugins] make plugin removal more predictable (thanks @ajkerrigan for fix)
    - [prev-sheet] would stack trace if more than one sheet loaded and no other sheet visited (thanks @frosencrantz for bug report #342)
    - [regex] will not silently fail if some example rows are not matches
    - [save] convert savers to use itervalues
        - itervalues(format=False) now yields OrderedDict of col -> value
            - value is typed value if format=False, display string if True
        - options.safety_first will convert newlines and tabs to options.tsv_safe_newline and options.tsv_safe_tab (thanks @mesibov for bug report #76)
    - [sheets] colorizer exceptions are now caught
    - [sheets] keycols now keep order they are keyed
    - [sysedit] trim all trailing newlines from external edits (thanks @sfranky for bug report #378)
    - [tsv] column name "length" prevented loading (thanks  @suhrig for bug report #344)
    - [undo] redo with cmd on first row did not move cursor (thanks @Mikee-3000 for bug report #339)
        - now row/col context are set as strings, even when they are numeric indices

## Infrastructure / API
    - [add-row] create a default newRow for Sheet (thanks @for-coursera for bug report #363)
    - [calc] add INPROGRESS sentinel
        - sentinel that looks like an exception for calcs that have not completed yet
    - [extensible] add new cached_property, which caches until clear_all_caches, which clears all cached_property
    - [Fanout] add Fanout
        - fan out attribute changes to every element in a list; tracks undo for list
    - [lazy_property] newSheet and cmdlog are now lazy_property
        - this enables the overwriting and extending of them by plugins
    - [loaders] add sheet.iterload()
        - will use sheet.source to populate and then yield each row
    - [loaders] vd.filetype(ext, ExtSheet) to register a constructor
    - [loaders] add Sheet.iterrows() to yield row objects 
        - grouping use iterrows() for streaming input
        - __iter__() yields LazyComputeRows
            ```
            for row in vd.openSource('foo.csv'):
                print(row.date, row.name)
            ```
    - [IndexSheet] refactor SheetsSheet parent to IndexSheet
        - HtmlTablesSheet now inherits from IndexSheet
        - excel index changed to standard IndexSheet model
        - VisiDataSheet changed into IndexSheet
        - move join-sheets to IndexSheet
    - [options] add unset() to unset options (thanks @khughitt for suggestion #343)
    - [path] consolidate PathFd, UrlPath, and HttpPath into Path
    - [SequenceSheet] refactor tsv, csv, xls(x), fixed_width to inherit from SequenceSheet
    - [sheets] vd.sheetsSheet is sheetstack, vd.allSheetsSheet is sheetpile
    - [sheets] rename LazyMap to LazyChainMap and LazyMapRow to LazyComputeRow
    - [shortcut] BaseSheet.shortcut now property
    - [status] make right status more configurable (thanks @layertwo #375 and khugitt #343 for filing issues)
        - BaseSheet.progressPct now returns string instead of int
        - BaseSheet.rightStatus() now returns string only (not color)
        - by default uses `options.disp_rstatus_fmt`, configured like `disp_status_fmt`
        - progress indicator (% and gerund) moved out of rightStatus and into drawRightStatus
    - [undo] use undofuncs to associate command with its undo
    - [undo/redo] moved to undo.py
    - [vd] add sheet properties for errors and statuses
    - [vd] vd.quit() now takes `*sheets`
    - [vd] rename main() to main_vd()

# v2.-1 (2019-08-18)

## Major changes

    - Minimum Python requirement bumped to 3.6
    - Several interface changes (see below)

## Major features

    - add Alt/Esc as prefix; Alt+# to go to that sheet
       - Alt+ layer not otherwise used; bind with `^[x` for Alt+X
    - undo/redo
        - [new command] `options.undo` (default: True) to enable infinite linear undo/redo
        - provisionally bound to `Shift+U` and `Shift+R`
        - will undo most recent modification on current sheet
        - `undoEditCells` assumes commands modified only selectedRows
    - multi-line rows
        - toggle by pressing `v` on any sheets with truncated values
    - range binning for numeric columns
        - `options.numeric_binning` (default: False) is the feature flag
        - [feature freqtbl] numeric binning for frequency/pivot table
        - `options.histogram_bins` to set number of bins (0 to choose a reasonable default)
        - (thanks @paulklemm for the issue #244)
    - stdout pipe/redirect
        - `ls|vd|lpr` to interactively select a list of filenames to send to the printer
        - `q`/`gq` to output nothing
        - `Ctrl+Q` to output current sheet (like at end of -b)
        - `vd -o-` to send directly to the terminal (not necessary if already redirected)
    - plugin framework
        - plugins are optional Python modules that extend or modify base VisiData's functionality
        - this release establishes a structure for creating plugins, and provides an interface within VisiData for installing them
            - `open-plugins` opens the **PluginsSheet**
            - to download and install a plugin, move the cursor to its row and press `a` (add)
            - to turn off a plugin, move the cursor to its row and press `d` (delete).
        - for more information see (https://visidata.org/docs/plugins)
    - deferred changes
        - modifications are now highlighted with yellow, until committed to with `^S` (`save-sheet`)

## interface changes

- `setcol-*`, `dive-selected`, `dup-selected-*`, `columns-selected`, `describe-selected` use only selectedRows (do not use all rows if none selected) #265 (thanks @cwarden)
- `edit-cells` renamed to `setcol-input`
- `fill-nulls` renamed to `setcol-fill`
- `paste-cells` renamed to `setcol-clipboard`
- `dup-cell`/`dup-row` on SheetFreqTable and DescribeSheet renamed to `dive-cell`/`dive-row`
- `next-page`/`prev-page` renamed to `go-pagedown`/`go-pageup`
- `save-col` always saves all rows in current column (instead of selectedRows or rows)
- `copy-*` use only selectedRows, warning if none selected (cmdlog safe)
- `syscopy-*` use only selectedRows, fail if none selected (not cmdlog safe)
- all `plot-selected` are now `plot-numerics`; `plot-numerics` uses all rows
- Shift+S pushes `sheets-stack`; gS pushes `sheets-all`. removed graveyard sheet.
- `random-rows` is no longer bound to any key by default (was Shift+R).
- `freq-summary` was `freq-rows`; adds summary for selected rows
- cmdlog is now based on longname instead of keystrokes
- cmdlog does not log resize commands
- exit with error code on error during replay (suggested by @cwarden #240)
- split `Ctrl+V` (check-version) into `Ctrl+V` (show-version) and `z Ctrl+V` (require-version)
- `show-expr` now unbound from `z=`
- add `options.row_delimiter` (default to `\n`)


## plugins

- vfake: anonymizes columns
- livesearch: filter rows as you search
- rownum: add column of original row ordering
- sparkline: add a sparkline column to visualise trends of numeric cells in a row (thanks @layertwo #297)

## Bugfixes

- [addcol-new] addcol-new now works in batch mode (thanks @cwarden for the bug report #251)
- [canvas] clipstr xname to prevent overlap with 1st element in xaxis
- [color] column separator color applies to regular rows (thanks @mightymiff for bug report #321)
- [DirSheet] delete-selected now deletes all of the selected files upon save-sheet (thanks @cwarden for the bug report #261)
- [display] fix resizing issue with wide chars (thanks @polm for the bug report #279 and for the fix #284 )
- [freqtbl] unselect-rows now updates source rows (thanks @cwarden for bug report #318)
- [go-col-regex] nextColRegex sheet is implicit parameter
- [help] use tab as sep for system sheets (thanks @frosencrantz for bug report #323)
- [plot] graphing currency values now works
- [pyobj] SheetDict nested editing (thanks @egwynn for the bug report #245)
- [txt] TextSheets now save as .txt
- [yaml] handle sources that do not load as lists (thanks @frosencrantz for bug report #327)
- [vdtui] make Sheet sortable (related to an issue found by @jsvine #241)


## Additions and improvements

- [addcol-new] does not ask for column name
- [aggr] add `list` aggregator (thanks @chocolateboy #263)
- [canvas] add legend width to fit max key (thanks @nicwaller for request)
- [chooseMany] error() on invalid choice #169
- [command join] add join-sheets-top2 (`&`) / join-sheets-all (`g&`) to Sheet to join top 2/all sheets in sheets-stack
- [command sort] `sort-*-add` bound to z[] and gz[] to add additional sort columns
- [command syspaste-cells] add `syspaste-cells` to paste into vd from system clipboard (thanks kovasap for PR #258)
- [describe] add `sum` (thanks @pigmonkey for suggestion #315)
- [DirSheet] include folders and hidden files
- [exec-longname] enable history
- [freeze-sheet] only freeze visibleCols
- [html] add links column where hrefs available (suggested by @am-zed #278)
- [license] remove MIT license from vdtui; all code now licensed under GPL3
- [loader fixed] provide a way to limit the max number of columns created (thanks @frosencrantz for suggestion #313)
    - added `options.fixed_maxcols` (default: no limit)
- [loader fixed] loaders override putValue, not setValue (thanks @aborruso for bug report #298)
- [loader jira] add suport for jira filetype, a markdown derivative compatible with Atlassian JIRA (thanks @layertwo #301)
- [loader Pyobj] `py` filetype to import and explore a python module: `vd -f py curses`
- [loader pyxlsb] add .xlsb loader (suggested by @woutervdijke #246)
- [loader ndjson ldjson] add as aliases for jsonl
- [loader npy] add .npy loader, including type detection
- [loader npz] add support for .npz index
- [loader usv] add .usv loader
- [macros] is now deprecated
- [motd] domotd is asyncsingle and thus not sync-able
- [mouse] bind Ctrl+scrollwheel to scroll-left/right; change to move cursor by `options.scroll_incr` (like scroll-up/down)
- [mouse] slide columns/rows with left-click and drag
- [openSource] create new blank sheet if file does not exist
- [option json] add `options.json_sort_keys` (default True) to sort keys when saving to JSON (thanks @chocolateboy for PR #262)
- [option regex+] `options.default_sample_size` (default 100) to set number of example rows for regex split/capture (now async).  use None for all rows. (thanks @aborruso #219)
- [option vd] `--config` option to specify visidatarc file (suggested by @jsvine #236)
- [option vdtui] remove `curses_timeout` option (fix to 100ms)
- [pandas] support multi-line column names (suggested by @jtrakk #223)
- [pandas] impement sort() for pandas DataFrame (suggested by @migueldvb #257)
- [pandas] use value_counts() for PandasSheetFreqTable (thanks @azjps for PR #267)
- [pandas] selection support for PandasSheet (thanks @azjps for PR #267)
- [pandas] reset index (thanks @danlat #277)
- [pandas] if the df contains an index column, hide it
- [pcap] adds saver for .pcap to json (thanks @layertwo for PR #272)
- [perf] expr columns are now set to cache automatically
- [perf] drawing performance improvements
- [perf] minor improvements to cliptext
- [perf] several minor optimisations to color
- [precious] describe-sheet is now precious; error-sheet and threads-sheet are not
- [replay] show comments as status (suggested by @cwarden)
- [save] make all `save_` callers async
- [sqlite] add save (CREATE/INSERT only; for wholesale saving, not updates)
- [sqlite] `Ctrl+S` to commit add/edit/deletes
- [sqlite] add support for .sqlite3 extension
- [tar] add support for opening tar files (thanks @layertwo #302)
- [vdmenu] `Shift+V` opens menu of core sheets
    - press `Enter` to open sheet described in current row
- [win] several changes made for increased windows-compatibility (thanks @scholer!)
- [yaml] bump min required version (thanks @frosencrantz for suggestion #326)


## API
- VisiData, BaseSheet, Column inherit from Extensible base class
  - internal modules and plugins can be self-contained
  - `@X.property @X.lazy_property`, `X.init()`, `@X.api`
- remove Sheet.vd; 'vd' attrs now available in execstr
- remove hooks
- add @deprecated(ver) decorator; put deprecations in deprecated.py
- `vd.sync(*threads)` waits on specific threads (returned by calls to `@asyncthread` functions)
- add Sheet.num for left status prompt
- pivot and frequency table have been consolidated for numeric binning
- add Sheet.nFooterRows property
- Sheet.column() takes colname instead of regex; add Sheet.colsByName cached property
- use addRow to rows.append in reload()
- Selection API is overloadable for subclasses of Sheet whose rows don't have a stable id() (like pandas)
- use locale.format_string and .currency
    - uses user default locale settings at startup
    - changes fmtstr back to %fmt (from {:fmt})
- vdtui broken apart into separate modules: editline, textsheet, cliptext, color, column, sheet
    - much code reorganization throughout
- convert all `vd()` to `vd`
- remove ArrayColumns, NamedArrayColumns
- urlcache now takes days=n
- Sheet.rowid
- add windowWidth and windowHeight
    - Sheets use their own .scr, in preparation for split-screen
- add VisiData.finalInit() stage
    - call vd.finalInit() at end of module imports to initialise VisiData.init() members
    - so that e.g. cmdlog is not created until all internal sheet-specific options has been set
- remove replayableOption() (now replay an argument within option())
- CursesAttr is now ColorAttr; ColorAttr now a named tuple
    - variables that contain a ColorAttr have been renamed from attr to cattr for readability
- improvements to scrolling API
- rename most cases of Sheet*/Column* to *Sheet/*Column
- use pathlib.Path in visidata.Path
- remove BaseSheet.loaded; add BaseSheet.rows = UNLOADED
- vd.push no longer returns sheet
- add @asyncsingle for asyncthread singleton

## Deps
- add submodule fork of pyxlsb for VisiData integration
- add amoffat/sh as submodule for vgit and vsh
- [postgres] swap for binary version of dep


# v1.5.2 (2019-01-12)

## Bugfixes
- [regex] fix `g*` #239 (thanks to @jsvine for bug hunting)
- [editline] suspend during editline will resume in editline
- [editline] `Ctrl+W` on an empty value in editline now works

## Docs
- [manpage] update the manpage to be more accurate for boolean command line options

# v1.5.1 (2018-12-17)

## Bugfixes
- [canvas] fix mouse right-click and cursor movement on canvas
- [idle performance] fix regression
- [columns] fix editing of "value" column on ColumnsSheet
- [describe] fix colorizer inheritance
- [csv] always create at least one column
- [pandas] fix pandas eval (`=`, etc) #208 (thanks to @nickray for suggesting)
- [pandas] preserve columns types from DataFrame #208 (thanks to @nickray for suggesting)
- [pandas] remove data autodetect #208 (thanks to @nickray for suggesting)

## Additions and changes
- [selection] `options.bulk_select_clear` per #229 (thanks to @aborruso for suggesting)
- [setcol-subst-all] add `gz*` to substitute over all visible cols (thanks to @aborruso for suggesting)
- [options] Shift+O now global options (was sheet options); `zO` now sheet options; `gO` now opens .visidatarc which can be edited (was global options)
- [sort] orderBy now asynchronous #207 (thanks to @apnewberry for suggesting)
- [fill] fill now async; uses previous non-null regardless of selectedness #217 (thanks to @aborruso for suggesting)
- [pandas] `options.pandas_filetype_*` passed to `pandas.read_<filetype>` (like `csv_*` to Python `csv` module) # 210 (thanks to @pigmonkey for suggesting)
- [rename-col-selected] `z^` now renames the current column to contents of selected rows (previously `gz^`); `gz^` now renames all visible columns to contents of selected rows #220 (thanks to @aborruso for suggesting)
- [vdtui null] show null display note in cells which match `options.null_value` (was only for None) # 213 (thanksto @aborruso for suggesting)
- [vdtui] visidata.loadConfigFile("~/.visidatarc") for use in REPL #211 (thanks to @apnewberry for suggesting)
- [progress] include thread name on right status during async
- [progress] add gerund to display (instead of threadname)
- [http] user specified filetype overrieds mime type
    - e.g. `vd https://url.com/data -f html`
- [clipboard] use `options.save_filetype` for default format



# v1.5 (2018-11-02)

## Bugfixes
- [clipboard] fix broken `gzY` (syscopy-cells)
- [cmdlog] always encode .vd files in utf-8, regardless of options.encoding
- [tsv] major `save_tsv` performance improvement
- [tsv] make short rows missing entries editable
- [shp] reset columns on reload
- [graph] shift rightmost x-axis label to be visible
- [http] allow CLI urls to have `=` in them
- [fixed width] truncate cell edits on fixed width sheets
- [aggregators] ignore unknown aggregators
- `visidata.view(obj)`: obj no longer required to have a `__name__`

## Additions and changes
- [save tsv json] errors are saved as `options.safe_error` (default `#ERR`)
   - if empty, error message is saved instead
- [plugins] `~/.visidata` added to sys.path on startup
   - put plugin in `~/.visidata/vdfoo.py`
   - put `import vdfoo` in `.visidatarc` to activate
- [aggregators] show-aggregate (`z+`) now aggregates selectedRows
- [tsv] add unnamed columns if extra cells in rows
- [diff] now based on display value (more intuitive)
- [mouse] move to column also
- [mouse] right-click to rename-col, rename-sheet, or edit-cell
- [cosmetic] addcol-new (`za`) input new column name on top of new column
- [cosmetic] include file iteration in progress meter
- [xls xlsx] use options.header to determine column names

# v1.4 (2018-09-23)

## Bugfixes

- batch mode with no script should use implicit stdin only if no other files given (Closed #182)
- [pivot] pivot keycolumn copy was yielding strange nulls
- [join] fix extend join
- [csv] include first row in file even if `options.header` == 0
- [sysclip] fix bug where `gzY` did not copy selected rows (Closed #186)
- [motd] fix bug with disabling `options.motd_url` (Closed #190)

## Additions and changes

- various improvements in performance and in CPU usage (Closed #184, #153)
- [pyobj] `visidata.view(obj)` and `visidata.view_pandas(df)`
- [pandas] `-f pandas` loads file with `pandas.read_<ext>`
- [TextSheet] wrap made consistent with new options
- [date] date minus date now gives float number of days instead of seconds
- [pcap] add support for reading pcapng (thanks @layertwo!)
- [setcol] limit `gz=` range parameters to the number of rows selected to be filled (thanks @ssiegel!)
- [anytype] format anytype with simple str()

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
    - `Ctrl+z` now undoes the most recent delete; `gCtrl+z` undoes all deletes
- Fix cursor row highlighting of identical rows

## v0.95.2
- move some functionality out of vdtui into seperate python files
- add Ctrl+z command to launch external $EDITOR
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
- change key for 'eval Python expression as new pyobj sheet' from Ctrl+O to Ctrl+X

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
