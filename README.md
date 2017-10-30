# VisiData v0.97.1 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

## Dependencies

- Linux or OS/X
- Python 3.4+
- python-dateutil
- other modules may be required for opening particular data sources

## Install

```
$ pip3 install visidata
```

## Run

```
$ vd [<options>] <input> ...
$ <command> | vd [<options>]
```

VisiData supports tsv, csv, xlsx, hdf5, sqlite, and more.
Use `-f <filetype>` to force a particular filetype.

## Documentation

* Quick reference: `F1` (or `z?`) within `vd` will open the [man page](http://visidata.org/man), which has a list of all commands and options.
* [visidata.org](http://visidata.org) has some [tours](http://visidata.org/tour)
* [VisiData Architecture for Developers](docs/architecture.rst)

## Support

- [r/visidata](https://www.reddit.com/r/visidata/) on reddit
- [#visidata]() on freenode.net

If something doesn't appear to be working right, please create [an issue on Github](https://github.com/saulpw/visidata/issues).  Include the full stack trace shown with `Ctrl-e`.

To contribute a bugfix or other code, fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls).

## Other vdtui projects

The core `vdtui.py` can be used to quickly create efficient terminal workflows.

- [vgit](https://github.com/saulpw/vgit): a git interface
- [vdgalcon](https://github.com/saulpw/vdgalcon): a port of the classic game [Galactic Conquest](https://www.galcon.com)

Other workflows should also be created as separate apps using vdtui.  These apps can be very small; for example, see the included [viewtsv](bin/viewtsv).


## License

The innermost core file, `vdtui.py`, is a single-file stand-alone library that provides a solid framework for building text user interface apps. It is distributed under the MIT free software license, and freely available for inclusion in other projects.

Other VisiData components, including the main `vd` application, addons, loaders, and other code in this repository, are available for reuse under GPLv3.

## Credits

VisiData was created by Saul Pwanson `<visidata@saul.pw>`.
Thanks to @anjakefala for test and release support, to @databranner for documentation, and to those wonderful users who contribute feedback in any form, for helping to make VisiData the awesome tool that it is.
