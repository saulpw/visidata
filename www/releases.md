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
