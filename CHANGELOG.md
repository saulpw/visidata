# VisiData version history

# v2.-4 (XXXX-XX-XX)

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
