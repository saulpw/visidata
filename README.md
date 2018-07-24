# VisiData v1.2.1 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

## Dependencies

- Linux or OS/X
- Python 3.4+
- python-dateutil
- other modules may be required for opening particular data sources
    - see [requirements.txt](https://github.com/saulpw/visidata/blob/stable/requirements.txt) or the [supported sources](http://visidata.org/man/#loaders) in the vd manpage

## Getting started

### Installation

Each package contains the full loader suite but differs in which loader dependencies will get installed by default.

The base VisiData package concerns loaders whose dependencies are covered by the Python3 standard library. Currently these include the loaders for tsv, csv, fixed width text, json, and sqlite. Additionally, .zip, .gz, .bz2, and .xz files can be decompressed on the fly.

|Platform           |Package Manager                        | Command                                       | Out-of-box Loaders   |
|-------------------|----------------------------------------|----------------------------------------------|----------------------|
|Python3.4+         |[pip3](https://visidata.org/install#pip3) | `pip3 install visidata`                    | Base                 |
|Python3.4+         |[conda](https://visidata.org/install#conda) | `conda install --channel conda-forge visidata` | Base, http, html, xls(x) |
|MacOS              |[Homebrew](https://visidata.org/install#brew) | `brew install saulpw/vd/visidata`            | Base, http, html, xls(x) |
|Linux (Debian/Ubuntu) |[apt](https://visidata.org/install#apt) | [click me](https://visidata.org/install#apt)                      | Base, http, html, xls(x) |
|Linux (Debian/Ubuntu) |[dpkg](https://visidata.org/install#dpkg) | [click me](https://visidata.org/install#dpkg)                | Base, http, html, xls(x) |
|Windows               |[WSL](https://visidata.org/install#wsl) | Windows is not yet directly supported (use WSL) | N/A |
|Python3.4+            |[github](https://visidata.org/install#git) | `pip3 install git+https://github.com/saulpw/visidata.git@develop` | Base |

Please see [/install](https://visidata.org/install) for detailed instructions, additional information, and troubleshooting.

### Usage

    $ vd [<options>] <input> ...
    $ <command> | vd [<options>]

VisiData supports tsv, csv, xlsx, hdf5, sqlite, json and more.
Use `-f <filetype>` to force a particular filetype.
(See the [list of supported sources](http://visidata.org/man#sources)).

### Documentation

* [VisiData v1.2 Getting Started Tutorial](https://jsvine.github.io/intro-to-visidata/) by [Jeremy Singer-Vine](https://www.jsvine.com/)
* Quick reference: `F1` (or `^H`) within `vd` will open the [man page](http://visidata.org/man), which has a list of all commands and options.
* [/docs](http://visidata.org/docs) contains a collection of howto recipes.

### Help and Support

If you have a question, issue, or suggestion regarding VisiData, please [create an issue on Github](https://github.com/saulpw/visidata/issues).

## vdtui

The core `vdtui.py` can be used to quickly create efficient terminal workflows. These have been prototyped as proof of this concept:

- [vgit](https://github.com/saulpw/vgit): a git interface
- [vsh](http://github.com/saulpw/vsh): a collection of utilities like `vping` and `vtop`.
- [vdgalcon](https://github.com/saulpw/vdgalcon): a port of the classic game [Galactic Conquest](https://www.galcon.com)

Other workflows should also be created as separate apps using vdtui.  These apps can be very small and provide a lot of functionality; for example, see the included [viewtsv](bin/viewtsv).


## License

The innermost core file, `vdtui.py`, is a single-file stand-alone library that provides a solid framework for building text user interface apps. It is distributed under the MIT free software license, and freely available for inclusion in other projects.

Other VisiData components, including the main `vd` application, addons, loaders, and other code in this repository, are available for use and distribution under GPLv3.

## Credits

VisiData was created and developed by Saul Pwanson `<vd@saul.pw>`.

Thanks to all the contributors, and to those wonderful users who provide feedback, for making VisiData the awesome tool that it is.
