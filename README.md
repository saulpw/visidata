[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/saulpw/visidata)

# VisiData v2-5dev [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/develop.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/develop)

A terminal interface for exploring and arranging tabular data.

![Frequency table](http://visidata.org/freq-move-row.gif)

## Dependencies

- Linux or OS/X
- Python 3.6+
- python-dateutil
- other modules may be required for opening particular data sources
    - see [requirements.txt](https://github.com/saulpw/visidata/blob/stable/requirements.txt) or the [supported sources](https://visidata.org/man/#loaders) in the vd manpage

## Getting started

### Installation

Each package contains the full loader suite but differs in which loader dependencies will get installed by default.

The base VisiData package concerns loaders whose dependencies are covered by the Python3 standard library.

Base loaders: tsv, csv, json, sqlite, and fixed width text.

|Platform           |Package Manager                        | Command                                       | Out-of-box Loaders   |
|-------------------|----------------------------------------|----------------------------------------------|----------------------|
|all         |[pip3](https://visidata.org/install#pip3) | `pip3 install visidata`                    | Base                 |
|all         |[conda](https://visidata.org/install#conda) | `conda install --channel conda-forge visidata` | Base, http, html, xls(x) |
|MacOS              |[Homebrew](https://visidata.org/install#brew) | `brew install saulpw/vd/visidata`            | Base, http, html, xls(x) |
|Linux (Debian/Ubuntu) |[apt](https://visidata.org/install#apt) | [full instructions](https://visidata.org/install#apt)                      | Base, http, html, xls(x) |
|Linux (Debian/Ubuntu) |[dpkg](https://visidata.org/install#dpkg) | [full instructions](https://visidata.org/install#dpkg)                | Base, http, html, xls(x) |
|Windows               |[WSL](https://visidata.org/install#wsl) | Windows is not directly supported (use WSL) | N/A |
|all            |[github](https://visidata.org/install#git) | `pip3 install git+https://github.com/saulpw/visidata.git@stable` | Base |
|Linux (NixOS)|[nix](https://visidata.org/install#nix)| `nix-env -i visidata`|Base, yaml, xls(x), hdf5, html, pandas, shp |

Please see [/install](https://visidata.org/install) for detailed instructions, additional information, and troubleshooting.

### Usage

    $ vd [<options>] <input> ...
    $ <command> | vd [<options>]

VisiData supports tsv, csv, xlsx, hdf5, sqlite, json and more (see the [list of supported sources](https://visidata.org/man#sources)).

Use `-f <filetype>` to force a particular filetype.


### Documentation

* [Intro to VisiData Tutorial](https://jsvine.github.io/intro-to-visidata/) by [Jeremy Singer-Vine](https://www.jsvine.com/)
* Quick reference: `Ctrl+H` within `vd` will open the [man page](https://visidata.org/man), which has a list of all commands and options.
* [keyboard list of commands](https://visidata.org/docs/kblayout)
* [/docs](https://visidata.org/docs) contains a collection of howto recipes.

### Help and Support

If you have a question, issue, or suggestion regarding VisiData, please [create an issue on Github](https://github.com/saulpw/visidata/issues) or chat with us at #visidata on [freenode.net](https://webchat.freenode.net/).

Here are some concrete ways you can help make VisiData even more awesome:

* Write a blogpost (or tweet or whatever) about a VisiData command or feature you use frequently, and share it with us!
* Expand VisiData to support .xyz proprietary data format.  Creating a loader [is really straightforward](http://visidata.org/docs/loaders/).
* Pandas users can [help improve the PandasSheet](https://github.com/saulpw/visidata/labels/pandas) with optimizations and pandas-specific integration.
* Create and maintain [new installation packages](https://github.com/saulpw/visidata/labels/packaging).
* Drive one of the tasks on the [maybe someday list](https://github.com/saulpw/visidata/issues?q=is%3Aissue+%5Bwishlist%5D+).
* Acknowledge the realities of late-stage capitalism and [give regular old money](https://www.patreon.com/saulpw).

## Other applications within the VisiData ecosystem

The core interface paradigm--rows and columns--can be used to create efficient terminal workflows with a minimum of effort for almost any application. These have been prototyped as proof of this concept:

- [vgit](https://github.com/saulpw/visidata/tree/stable/plugins/vgit): a git interface
- [vsh](https://github.com/saulpw/vsh): a collection of utilities like `vping` and `vtop`.
- [vdgalcon](https://github.com/saulpw/vdgalcon): a port of the classic game [Galactic Conquest](https://www.galcon.com)

Other workflows can also be created as separate apps using the visidata module.  These apps can be very small and provide a lot of functionality; for example, see the included [viewtsv](https://visidata.org/docs/viewtsv).

## License

VisiData, including the main `vd` application, addons, loaders, and other code in this repository, is available for use and redistribution under GPLv3.

## Credits

VisiData is conceived and developed by Saul Pwanson `<vd@saul.pw>`.

Anja Kefala `<anja.kefala@gmail.com>` maintains the documentation and packages for all platforms.

Many thanks to numerous other [contributors](https://visidata.org/credits/), and to those wonderful users who provide feedback, for helping to make VisiData the awesome tool that it is.
