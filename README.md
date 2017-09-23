# VisiData v0.96 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

<a href="https://github.com/saulpw/visidata/blob/develop/docs/tours.rst">![VisiData silent demo](docs/img/birdsdiet_bymass.gif)</a>

## Dependencies

- OS/X or Linux
- Python 3.4+
- other modules may be required for opening particular filetypes

# Install

```
$ pip3 install visidata
```

# Run

```
$ vd [<options>] <input> ...
$ <command> | vd [<options>]
```

Unknown filetypes are by default viewed with a text browser.  Use `-f <filetype>` to force a particular filetype.  VisiData supports tsv, csv, xlsx, hdf5, sqlite, and more.

VisiData supports 256-color terminals.  Use [`vdcolor`](github.com/saulpw/visidata/stable/bin/vdcolor) to browse the available colors.

## Replay Script

To replay a [.vd script](https://github.com/saulpw/visidata/tree/develop/tests) (saved previously with `^D`), which may be parameterized with Python string formatting `{field}`s:

```
$ vd [<options>] --play <script.vd> [<format>=<value> ...]
```

## [User Reference Manual](http://visidata.org/man/vd)

The comprehensive user reference is the [man page](http://visidata.org/man/vd), accessible from the terminal with:

```
$ export MANPATH=~/.local/man   # PEP370 or wherever installed
$ man vd
```

The manual includes a list of all commands and options.  A few interesting commands:

* `Shift-F` pushes a frequency analysis of the current column
* `=` creates a new column from the given Python expression (use column names to refer to their contents)
* `;` creates new columns from the match groups of the given regex

# Developers

If something doesn't appear to be working right, please create [an issue on Github](https://github.com/saulpw/visidata/issues).  Include the full stack trace shown with `Ctrl-e`.

To contribute a bugfix or a loader for another file format, fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls).  Here is the [developer documentation for loaders](http://visidata.org/dev#loaders).

## Other vdtui projects

The core `vdtui.py` can be used to quickly create efficient terminal workflows.

- [vgit](https://github.com/saulpw/vgit): a git interface
- [vdgalcon](https://github.com/saulpw/vdgalcon): a port of the classic game [Galactic Conquest](https://www.galcon.com)

Other workflows should be created as separate [apps using vdtui](docs/architecture.rst).  These apps can be very small; for example, see the included [viewtsv](bin/viewtsv).

## Community

- [r/visidata](https://www.reddit.com/r/visidata/)
- [#visidata]() on freenode.net
- [mailing list]()

## License

The innermost core file, `vdtui.py`, is a single-file stand-alone library that provides a solid framework for building text user interface apps. It is distributed under the MIT free software license, and freely available for inclusion in other projects.

Other VisiData components, including the main `vd` application, addons, loaders, and other code in this repository, are available for reuse under GPLv3.

## Credits

VisiData was created by Saul Pwanson `<visidata@saul.pw>`.
Thanks to @anjakefala for test and release support, to @databranner for documentation, and to those wonderful users who contribute feedback and in any form, for helping to make VisiData the awesome tool that it is.
