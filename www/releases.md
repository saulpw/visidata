
# [v1.3.1](https://github.com/saulpw/visidata/releases/tag/v1.3.1) (2018-08-19)

We found some issues with 1.3 (aggregators interacting with nulls/errors, primarily) that we didn't want to let sit until 1.4.  So we fixed those issues and a couple others, and added a few 'minor' features.  This patch version should be a definitive improvement over the base 1.3 version.

The complete list of changes is in the [CHANGELOG](https://github.com/saulpw/visidata/blob/stable/CHANGELOG.md).  Here are the new options and features:

- new `extend` join type keeps the type of the first sheet, extending it with columns from the other sheets
- `rename-sheet` command (thanks to @jsvine for suggestion; what default keybinding should it have?)
- [DirSheet] add `reload-rows` (`gz^R`) to undo modifications on all selected rows
- remove all options.foo_is_null and add options.null_value
- options.save_errors (default True) to include errors when saving
- add options.json_indent for json pretty-printing

# [v1.3](https://github.com/saulpw/visidata/releases/tag/v1.3) (2018-08-11)

It's been a productive 3 months since v1.2.  The largest effort in this release was a commands/options reworking, which will hopefully pay dividends in the future.  Many other so-called improvements were made as well.  Here's a list of most of them:

### commands

- All commands were thoughtfully renamed, and the command longnames should be largely stable now.
- [`commands.tsv`](https://raw.githubusercontent.com/saulpw/visidata/stable/visidata/commands.tsv) is an exhaustive list of commands and their attributes and side effects.
- The manpage has moved to `Ctrl+H` (sysopen-help), which is hopefully its final keybinding.
   - `F1` will still open the manpage if the terminal doesn't intercept it.
   - but `z?` has been repurposed (see below).
   - Note that because iTerm reports `Ctrl+H` as `Backspace`, these help commands are also available by using `Backspace` (backspace for help, a new trend).
- `z Ctrl+H` opens a list of commands available on this sheet.
- Keybindings and longnames are separated out.  The cmdlog now records longnames as well.
- See the new [keyboard layouts page](http://visidata.org/docs/kblayout/) (thanks to @deinspanjer for inspiration).

### changes to existing commands and options

- The experimental menu system (was `Space`) has been removed.
- Now `Space` (exec-longname) executes the command for the input longname (tab completion of available commands is supported).  (This function was previously bound to `Ctrl+A`).
- `options.wrap` (for TextSheet wrapping of lines) now defaults to `False`.
- `R` (random-sheet) opens a new sheet instead of selecting random rows (reverting to former behavior).
- `za` (addcol-empty) asks for column name
- `zd` (delete-cell) moves value to clipboard ("cut", like other delete commands)

### options

- options can now be set on specific sheet types or even individual sheets.  `Shift+O` opens [options for the current sheet type](http://visidata.org/docs/customize/), and `g Shift+O` opens the global options sheet.
- See available colors by pressing `Space` and then typing the longname `colors`.

#### new safety options

- Error messages are sorted before informational status messages, and colored by `color_error` and `color_warning` (thanks to @jsvine for suggestion)
- `options.quitguard` (default `False` to keep old behavior) if True, will confirm before quitting last sheet.
- The `gS` (sheets-graveyard) command opens a sheet that shows all discarded (but "precious") sheets.  These are stored as weak references so they will be garbage collected eventually, but can be resurrected from the graveyard sheet until then.
- `options.safety_first` (default `False`) makes loading/saving more robust, likely at the cost of performance which can become significant in large files.
   - Currently, only removes NULs from csv input.
- `options.tsv_safe_char` is split into `tsv_safe_newline` and `tsv_safe_tab`.

### new power features

- `z;` (`addcol-sh`) adds new columns for stdout/stderr of a `bash` command, which uses `$colname` to substitute values from other columns (whole arguments only, so far).
- `z|` (`select-expr`) and `z\` (`unselect-expr`) select/unselect by Python expression (thanks to @jsvine for suggestion).
- `z/` (`search-expr`) and `z?` (`searchr-expr`) to search forward/backward by Python expression.
- `gI` (`describe-all`) describes all columns in all sheeets (like `gC` (`columns-all`)).

### nice things
- The `g(`, `z(`, and `gz(` variants of `(` ('expand-column') are filled out.
- `z#` sets type of current column to `len`.

## new loaders

- yaml loader (thanks to @robcarrington, @JKiely, @anjakefala at PyCon Sprints for making this happen)
- pcap loader (thanks to @vbrown608 and @TemperedNetworks)
- xml loader
- jsonl saver
- [json loader] no more incremental display (need a better json parser than the Python stdlib offers)
- [pandas adapter](https://github.com/saulpw/visidata/issues/162#issuecomment-400488487) (thanks to @jjzmajic for issue #162)

## minor changes

- System clipboard command detection is more portable (thanks to @chocolateboy for the PR).
- `date` supports adding a number of days (or like `foo+6*hours`, `foo+9*months`, etc).
- Hidden columns are darkened on columns sheet.
- Exceptions are rolled up properly.
- `options.motd_url` now uses https by default (thanks to @jsvine for the warning).
- [DirSheet] `mode` is editable (set to octal like `0o0644`).
- [internal dev] ProfileSheet is improved.

## known issues

* cmdlog replay with a `Ctrl+S` (`save-sheet`) to an existing file gets stuck in an infinite loop when `options.confirm_overwrite` is on.
* After renaming a file on a **DirSheet**, `Ctrl+R` (`reload-sheet`) is required to refresh the `ext` column for that row.
* `n`/`N` (`next-search`/`prev-search`) won't continue a previous `search-expr` and `searchr-expr`.
* `show-aggregate` with *mean* errors on `int` columns.
* Contracting (with `)`) a previously expanded column on a dup-ed (with `"`) sheet results it in disappearing on the source sheet.

# [v1.2.1](https://github.com/saulpw/visidata/releases/tag/v1.2.1) (2018-07-06)

@deinspanjer (issue [#164](https://github.com/saulpw/visidata/issues/164)) discovered that VisiData doesn't work with Python3.7 due to our use of the 'async' identifier, which is now off-limits as it is a formal keyword as of 3.7. The only change in 1.2.1 is changing 'async' to 'asyncthread' in order to work with Python 3.7.

Thanks to the illustrious @anjakefala for getting this release out quickly and without incident (knock on wood).


# [v1.2](https://github.com/saulpw/visidata/releases/tag/v1.2) (2018-05-03)

Here are the major feature enhancements for v1.2.  Please see the [CHANGELOG](https://github.com/saulpw/visidata/blob/stable/CHANGELOG.md) for the complete list.

## Major features

* DirSheet enhancements (modify file metadata, move/delete files)
* multisave (single file multisave to html, md, and txt format, or into a directory for other formats)
* prototype macro system with `z^S` on the commandlog
* [New conda package](https://github.com/conda-forge/visidata-feedstock)

## New commands and options

* `T` to push derived sheet with transposed rows/columns
* `zs`/`zt`/`zu` to select/unselect/toggle rows from top of sheet to cursor (thanks @SteveJSteiner for the suggestion)
* `gzs`/`gzt`/`gzu` to select/unselect/toggle rows from bottom to cursor
* `gv` to unhide all columns
* `gM` to melt into multiple value columns
* `g*` to transform selected rows in place
* `z<`/`z>' to move up/down to next null cell
* `^A` to execute a command by its longname
* `gD` to open the directory at `options.visidata_dir` (default `~/.visidata`)

### options

* `options.cmdlog_histfile` to specify a file to auto-append commandlog to (default empty means disabled)
* `options.tsv_safe_char` to replace tabs and newlines when writing .tsv format (default empty means disabled, for faster saving)
* `options.error_is_null` to count errors as null (default false)

## New supported formats and sources

* sas7bda (SAS; requires `sas7bdat`)
* xpt (SAS; requires `xport`)
* sav (SPSS; requires `savReaderWriter`)
* dta (Stata; requires `pandas`)
* bz2 and xz (LZMA) compression (thanks @jpgrayson)

# [v1.1](https://github.com/saulpw/visidata/releases/tag/v1.1) (2018-03-06)

This is the first release since 1.0.  The major additions and changes:

- All external loader dependencies have been removed from the PyPI, brew, and Debian packages.  This will make for much faster initial installation.
   - The json, csv, tsv, and sqlite loaders are still available with the base installation as they are supported by the Python standard library.  Other loaders will need their dependencies to be installed manually.  See [requirements.txt](https://github.com/saulpw/visidata/blob/stable/requirements.txt) for which external packages to install for each loader.

- An experimental command menu is now available via `Space`. The goal is to make it easier for people to explore the available functionality, and to try commands without knowing their keybindings.
   - Use the standard VisiData movement keys (`h`/`l`/Arrows, `q` to back out)
   - The help strings are shown during navigation, along with the available keybindings, so this will hopefully help people learn the keybindings as they use commands, without having to break their flow to refer to the manpage.
   - Commands are organized in a hierarchy according to their longnames.  This hierarchy may change in future releases, so these longnames are not yet stable enough to use for command aliases or in cmdlog replay.  The actual command keys are more stable and should be preferred for the time being.
   - If you play with the menu system, please let me know what did or didn't work for you!

- The `Y` command series was added to copy ("yank") to the system clipboard (with `options.clipboard_copy_cmd`, set to `pbclip` for MacOS by default) to conveniently paste data in any supported text output format.
   - `Y` copies the current row, `zY` copies the current cell, and `gY` copies all selected rows (or all rows).
   - This mirrors the existing `y` command series, which yanks to VisiData's internal clipboard.

- `-` now works as a filename to specify stdin/stdout.  Useful especially in batch mode to dump final sheet to stdout (`-b -o -`).

New supported formats:

- markdown (`md`) is now supported for saving (but not loading, yet) to an org-mode compatible table format.

- .png files can now be loaded and saved, and crudely viewed on the canvas with an overloaded `.`.  The pixels can be edited on the source sheet like any other data.

- .ttf and .otf (font) files can be loaded and viewed on the canvas.  This is super useful for just about no one, but it was a great excuse to implement `Canvas.qcurve()`.

These commands have been added or changed, and are expected to stay in future versions:

- The `za` command adds an empty, editable column to any sheet.  `gza` adds N new columns.

- The `(` and `)` commands will expand/collapse list/dict columns (e.g. in nested json).

- In the canvas, `d` deletes points from source sheet that are contained within the cursor.  `gd` deletes all points shown on the screen.

- The `!@#$%-_` special actions on the Columns Sheet and Describe Sheet have been removed.  They were sometimes convenient, but more often made it difficult to interact with the Columns Sheet itself.
    - The `g` forms of these commands are still available and will operate on the source columns (with the exception of `g_`, which now works consistently on all sheets as expected).

- The `Shift+Arrows` are aliased to `HJKL` (though these may not work in all environments).

These additions are more experimental and may not stay in future versions:

- The `Backspace` command drops the current sheet (like `q`), and also scrubs its history from the cmdlog.

- `ENTER` is now aliased to `modify-edit-cell` by default.

Other minor changes:

- search and select with no input now uses the most recent input.  `n`/`N` do this already for row search (as before), but the new behavior works more like standard vim/less/etc tools, and also applies to non-row search (like `c`).

- Many sheets (pivot, describe, melt, and many loaders) have improvements and bugfixes to make them even better.

Finally, some other news:

- VisiData has been accepted into Debian for the next release!  It is currently available if you've added the `unstable` repo; install with `apt install visidata`.

- [Jeremy Singer-Vine has put together a great tutorial](https://jsvine.github.io/intro-to-visidata/) for people who want a smoother path to start using VisiData.

Thanks to everyone who contributed to this release!  As always, feedback and suggestions are welcome and appreciated.

---

# [v1.0](https://github.com/saulpw/visidata/releases/tag/v1.0) (2018-01-25)

VisiData 1.0 has been officially released!  Changes since the 0.99 release candidate:

- a complete overhaul of [the website](http://visidata.org) and [documentation](http://visidata.org/docs);
- a 2x across-the-board performance improvement for async threads (from disabling profiling by default);
- removed support for .visidatarc in the current directory and via XDG; only `$HOME/.visidatarc` is used now;
- many bugfixes, both functional and cosmetic;
- removed the "visidata[full]" package from PyPI;
- a [homebrew package](https://github.com/saulpw/homebrew-vd) (so you can now do `brew install saulpw/vd/visidata` on MacOS), and an [apt package](https://github.com/saulpw/deb-vd) that is under review for inclusion in Debian.

This is a huge milestone for VisiData.  I devoted my sabbatical (the entire year of 2017) to creating an open-source tool that would be useful for myself and other terminal users, and it was very important for me to release a stable and lasting 1.0 so that it could be set aside when I resumed working.

We could have gotten away without certain features and with fewer [supported formats](http://visidata.org/man#loaders), but there is such breadth and depth included in 1.0 (as shown by demos like [this one at the PyCascades 2018 conference](https://www.youtube.com/watch?v=N1CBDTgGtOU)), that I'm hard-pressed to choose which features should have been omitted.

I owe a great deal to many people who have helped and supported me through this process. VisiData would not be what it is without them.
[The list of contributors](http://visidata.org/about#credits) includes everyone who has submitted to the repository, but there are some other groups to whom VisiData and I are eternally indebted:

- the [Recurse Center](http://recurse.com), for maintaining an awesome space and incredibly supportive community that I am lucky to have become a part of;
- [Office Nomads](http://officenomads.com/), my local co-working space where I could work without turning into [Jack Torrance](https://www.youtube.com/watch?v=4lQ_MjU4QHw);
- and the [Python community](https://www.python.org/), for creating such a broadly useful language and ecosystem, without which VisiData would not be nearly as powerful.

Finally, a very special thanks to [Anja](https://github.com/anjakefala) for her incredible help in putting together the website, documentation, tests, and various releases.

Share and enjoy!

---

# [v0.99](https://github.com/saulpw/visidata/releases/tag/v0.99) (2017-12-22)

This is a 1.0 release candidate.

No changes will be made on stable before 1.0 except for targeted bugfixes with minimal likelihood of regressing anything else.  If there are any more bugfixes to be applied, they will be cherry-picked from continuing develop.  Either v0.99 or v0.99.1 will become the formal 1.0 in a few weeks.

User-facing changes in this version:

- tab completion for filename and python expressions
- load .html table elements (requires lxml)
  - http urls are now usable as sources (requires requests)
- save as .json
- `^W` to erase a word in the line editor
- `gC` views all columns on all sheets
- `median` aggregator
- `v` now 'visibility toggle' (moved from `w`)
- `--version` (thanks to @jsvine)
- `options.use_default_colors` (thanks to @wavexx)

---

# [v0.98.1](https://github.com/saulpw/visidata/releases/tag/v0.98.1) (2017-12-04)

v0.98.1 is a patch release that fixes a couple of minor bugs.  The primary change in this release, however, is that the 'visidata' package on PyPI no longer includes all of the loaders' dependencies by default.

This is a minor hassle for first-time users if they want to use certain formats, but since the goal is eventually supporting every possible data format, installing all dependencies for all users by default is not tenable.  The base VisiData already includes support for tsv, csv, fixed width, sqlite, graphs and more.  Most users will only need one or two additional dependencies.

To install VisiData with all dependencies for all loaders:

    pip3 install "visidata[full]"

Of course, you can install just the dependencies you need.  See ["SUPPORTED SOURCES"](http://visidata.org/man/#loaders) in the manpage for which packages to install.

---

# [v0.98](https://github.com/saulpw/visidata/releases/tag/v0.98)  (2017-11-23)

Title: VisiData v0.98, now with graphs and maps (experimental)

When I announced that v0.97 was "feature complete", I must have been talking about vdtui.
vdtui has been pretty stable, even as VisiData has added a low-resolution pixel canvas
(using Braille unicode characters) to draw graphs and maps.  In fact, apart from a few bug
fixes and small API changes, the only addition to vdtui in v0.98 is basic mouse support.

Here's a list of what's new in VisiData v0.98:

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

---

# [v0.97.1](https://github.com/saulpw/visidata/releases/tag/v0.97.1) (2017-10-29)

It's VisiData's 1st birthday! I started working on VisiData 1 year ago today (Oct 29).

v0.97.1 has only a few small patches:

- Fixed help manpage on OS/X (man has no --local-file option)
- Fixed Postgres (incomplete lazy import)
- Fixed ENTER on SheetsSheet on SheetsSheet to be no-op
- Fixed readthedocs redirect to visidata.org

---

# [v0.97](https://github.com/saulpw/visidata/releases/tag/v0.97) (2017-10-06)


**Important** If you like VisiData, sign up for the [newsletter](https://tinyletter.com/visidata)!

## Community

- I'm hanging out in #visidata on freenode! Come by and say hi if you use VisiData. I'd love to know how you're using it!

- r/visidata (on reddit) is the forum for longer-form discussion.

- See the new webpage at [visidata.org](http://visidata.org)! We migrated away from RTD, as it was too much hassle and limited our functionality.

- We have some example tours generated from our automated tests. See [visidata.org/tour](http://visidata.org/test). More will be coming with the next release!

## v0.97 has been released

The main themes for this release are:
1) commandlog replay fully operational (now running both automated tests and generating tours)
2) a quick ref guide in man page format (available in visidata via F1, and also online at [visidata.org/man](http://visidata.org/man)
3) [visidata.org](http://visidata.org) is now the primary home page (we've transitioned away from readthedocs)

There are also the usual suspects: new loaders, new commands, new options, and too many improvements and bugfixes to name. It is getting ever easier to write a new command or loader in a few minutes and have it just work.

With this release, VisiData is *feature complete*. There will still be many reworkings, interface changes, added commands, tweaks, embellishments, arguments, and explanations, but as far as I can see, all of the functionality is now there. We are inching ever closer to a v1.0 that will hopefully stand the test of time.

The main goals for the next release (v0.98) are 1) a set of great tours, and 2) documentation of the internal architecture: design decisions, implementation guidelines, and API references.

Here are some more detailed descriptions of what comes with this release:

## New Loaders

- simple remote postgres loader (vd postgres://user:password@dbserver.com:6254/database)

- fixed width column detection (ls -al | vd -f fixed --skiplines 1)

## New Commands and Options

- F1 launches man page quick ref (gF1 now opens the command sheet)

- vd --diff A B shows B with changes from A in red

- a Describe Sheet with 'I' shows basic stats for every column!

- streamlined commandlog (previously called editlog) functionality
- ^D to quickly save the current cmdlog; vd -p cmdlog-1.vd to replay it
- removed movement commands (use --replay-movement to reinsert movements)
- player piano with --delay (used to make the tours on the website)

- advanced editing, can now make new sheets from whole cloth!
- 'A' to add a new sheet with some number of columns
- 'a' to add a new empty row
- 'gz=' set this column in selected rows to values from a python list expression
- 'Del'/gDel to clear a cell (set a value to None)
- 'y' to yank/delete row; 'p' to paste
- 'zy' to yank (copy) cell contents; 'zp' to paste ('gzp' to paste to all selected rows)
- 'f' to fill null cells with the previous non-null value

---

# [v0.96](https://github.com/saulpw/visidata/releases/tag/v0.96) (2017-08-23)

# [v0.93](https://github.com/saulpw/visidata/releases/tag/v0.93) (2017-07-30)

* Fix display/feel bugs in `editText`
* Remove BACKSPACE for editlog undo
* Fix colorizer API
* Add `ctrl-u` command to toggle profiling of main thread
* Fix Column statistics (`options.col_stats` still disabled by default)

# [v0.92](https://github.com/saulpw/visidata/releases/tag/v0.92) (2017-07-11)

# [v0.91](https://github.com/saulpw/visidata/releases/tag/v0.91) (2017-06-29)

# [v0.61](https://github.com/saulpw/visidata/releases/tag/v0.61) (2017-06-11)

# [v0.41](https://github.com/saulpw/visidata/releases/tag/v0.41) (2017-01-18)

# [v0.37](https://www.reddit.com/r/pystats/comments/5hpph6/please_help_test_my_new_cursestextmode_data/) (2017-12-11)

# [v0.31.1](https://github.com/saulpw/visidata/releases/tag/v0.31.1) (2016-11-29)

# v0.14 (2016-11-13)
