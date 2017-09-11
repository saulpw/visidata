# VisiData v0.96 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

<a href="https://github.com/saulpw/visidata/blob/develop/docs/tours.rst">![VisiData silent demo](docs/img/birdsdiet_bymass.gif)</a>

## Dependencies

- OS/X or Linux
- Python 3.4+
- other modules are required for opening particular filetypes

# Install

```
$ pip3 install visidata
```

# Run

```
$ vd [<options>] <input> ...
$ <command> | vd [<options>]
```

Unknown filetypes are by default viewed with a text browser.  Use `-f <filetype>` to force a particular filetype.  VisiData supports tsv, csv, xlsx, hdf5, sqlite, ...

Here is the [options list](https://visidata.org/man/vd#options).

VisiData supports 256-color terminals.  Use [`vdcolor`](github.com/saulpw/visidata/stable/bin/vdcolor) to browse the available colors.

## Replay Script

To replay a previously [saved .vd script](https://github.com/saulpw/visidata/tree/develop/tests), which may be parameterized with `{format-field}`s:

```
$ vd [<options>] --play <script.vd> [--<format-field>=<value> ...]
```

`<script.vd>` should be `-` if piped through stdin.

## User Documentation

```
$ man vd
$ man 2 vd 
```

The contents of the man page are also available at [online](https://visidata.org/man).

Here is a [quick reference of all commands](https://github.com/saulpw/visidata/blob/stable/docs/ascii-commands.txt).  A few interesting ones:

* `Shift-F` pushes a frequency analysis of the current column
* `=` creates a new column from the given Python expression (use column names to refer to their contents)
* `;` creates new columns from the match groups of the given regex

# Developers

If something doesn't appear to be working right, please create [an issue on Github]().  Include the full stack trace shown with `Ctrl-e`.

To contribute a bugfix or a loader for another file format, fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls).  Here is the [developer documentation for loaders]().


## Other vdtui projects

The core `vdtui.py` can be used to quickly create efficient terminal workflows.

- [vgit](https://github.com/saulpw/vgit): a git interface
- [vdgalcon](https://github.com/saulpw/vdgalcon): a port of the classic game [Galactic Conquest](https://www.galcon.com)

Other workflows should be created as separate [apps using vdtui](docs/vdtui-dev.md).  These apps can be very small; for example, see the included [viewtsv](bin/viewtsv) which is only one page of code.

Designs for other tools are being considered.

## Community

- [#visidata]() on freenode.net
- [r/visidata](https://www.reddit.com/r/visidata/)
- [mailing list]()

## License

The innermost core file, `vdtui.py`, is a single-file stand-alone library that provides a solid framework for building text user interface apps. It is distributed under the MIT free software license, and freely available for inclusion in other projects.

Other VisiData components, including the main `vd` application, addons, loaders, and other code in this repository, are available for reuse under licensed under GPLv3.

## Credits

VisiData was created by Saul Pwanson `<visidata@saul.pw>`.  Thanks to @anjakefala for test and release support, to @databranner for documentation, and to those wonderful users who contribute feedback and in any form, for helping to make VisiData the awesome tool that it is.

