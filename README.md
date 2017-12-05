# VisiData v0.98.1 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

## Dependencies

- Linux or OS/X
- Python 3.4+
- python-dateutil
- other [modules may be required](https://github.com/saulpw/visidata/blob/stable/requirements.txt) for opening particular data sources
    - for a breakdown, see [supported sources](http://visidata.org/man/) in the VisiData manpage

## Install

To install VisiData, with loaders for formats supported by the Python standard library (which includes csv, tsv, fixed-width text, json, sqlite and graphs):

```
$ pip3 install visidata
```

To install VisiData, plus external dependencies for all available loaders:

```
pip3 install "visidata[full]"
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
* [visidata.org](http://visidata.org) has [asciicasts of its tests](http://visidata.org/test), which serve as example workflows.

## Support

If you want to chat about VisiData, make a feature request, or submit a bug report, we can be reached on either IRC or Reddit:

- [r/visidata](https://www.reddit.com/r/visidata/) on reddit
- [#visidata](irc://freenode.net/#visidata) on [freenode.net](https://webchat.freenode.net)

For more detailed information about how you can contribute as a developer, influence the roadmap as a user, or provide us with sufficient information to better support you through any issues you come across see the [CONTRIBUTING.md](CONTRIBUTING.md).

## vdtui

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
