# VisiData v0.98.1 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

## Dependencies

- Linux or OS/X
- Python 3.4+
- python-dateutil
- other modules may be required for opening particular data sources
    - see [requirements.txt](https://github.com/saulpw/visidata/blob/stable/requirements.txt) or the [supported sources](http://visidata.org/man/#loaders) in the vd manpage

## Installation

There are three options for installing visidata:
- [pip3](https://github.com/saulpw/visidata/tree/develop#install-via-pip3) for users who wish to import visidata into their own code or wish to integrate it into a python virtual environment
- [Homebrew](https://github.com/saulpw/visidata/tree/develop#install-via-brew) on MacOS/X for reliable installation of application components (such as the manpage)
- [apt](https://github.com/saulpw/visidata/tree/develop#install-via-apt) on Linux distributions

### Install via pip3

Best installation method for users who wish to take advantage of VisiData in their own code, or integrate it into a Python3 virtual environment.

To install VisiData, with loaders for the most common data file formats (including csv, tsv, fixed-width text, json, sqlite, http, html and xls):

```
$ pip3 install visidata
```

To install VisiData, plus external dependencies for all available loaders:

```
pip3 install "visidata[full]"
```

### Install via brew

Ideal for MacOS users who primarily want to engage with VisiData as an application. This is currently the most reliable way to install VisiData's manpage on MacOS.

```
brew install devotees/vd/visidata
```

Further instructions available [here](https://github.com/devotees/homebrew-vd).

### Install via apt

Packaged for Linux users who do not wish to wrangle with PyPi or python3-pip.

Currently, VisiData is undergoing review for integration into the main Debian repository. Until then it is available in our [Debian repo](https://github.com/devotees/deb-vd).

Grab our public key

```
wget http://visidata.org/devotees.gpg.key
apt-key add devotees.gpg.key
```

Add our repository to apt's search list

```
sudo apt-get install apt-transport-https
sudo vim /etc/apt/sources.list
    deb[arch=amd64] https://raw.githubusercontent.com/devotees/deb-vd/master sid main
sudo apt-get update
```
You can then install VisiData by typing:

```
sudo apt-get install visidata
```

Further instructions available [here](https://github.com/devotees/deb-vd).

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

Thanks to all the [contributors](CONTRIBUTING.md#contributors), and to those wonderful users who provide feedback, for making VisiData the awesome tool that it is.
