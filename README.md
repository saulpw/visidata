# VisiData v1.2.1 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A terminal interface for exploring and arranging tabular data.

## Dependencies

- Linux or OS/X
- Python 3.4+
- python-dateutil
- other modules may be required for opening particular data sources
    - see [requirements.txt](https://github.com/saulpw/visidata/blob/stable/requirements.txt) or the [supported sources](http://visidata.org/man/#loaders) in the vd manpage

### Install via pip3

Best installation method for users who wish to take advantage of VisiData in their own code, or integrate it into a Python3 virtual environment.

To install VisiData, with loaders for the most common data file formats (including csv, tsv, fixed-width text, json, sqlite, http, html and xls):

    $ pip3 install visidata

### Install via conda

To install from [conda-forge](https://github.com/conda-forge/visidata-feedstock):

Add the `conda-forge` channel.

    $ conda config --add channels conda-forge

You can then install VisiData by typing:

    $ conda install visidata

And update VisiData with:

    $ conda update visidata

### Install via brew

Ideal for MacOS users who primarily want to engage with VisiData as an application. This is currently the most reliable way to install VisiData's manpage on MacOS.

    $ brew install saulpw/vd/visidata

Further instructions available [here](https://github.com/saulpw/homebrew-vd).

### Install via apt

Packaged for Linux users who do not wish to wrangle with PyPi or python3-pip.

Currently, VisiData v1.0 is in Debian unstable's [main repository](https://launchpad.net/ubuntu/+source/visidata). If you want more up-to-date versions of VisiData, it will be available in our own [Debian repo](https://github.com/saulpw/deb-vd).

To install from Debian:

Obtain the public key

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8B48AD6246925553

Ensure the repository is in apt's search list

    $ sudo apt install apt-transport-https
    $ sudo vim /etc/apt/sources.list

      deb http://ftp.debian.org/debian/ unstable main

    $ sudo apt update

You can then install VisiData by typing:

    sudo apt install visidata

Instructions for installing from our own personal repository are available [here](https://github.com/saulpw/deb-vd).

## Usage

    $ vd [<options>] <input> ...
    $ <command> | vd [<options>]

VisiData supports tsv, csv, xlsx, hdf5, sqlite, json and more.
Use `-f <filetype>` to force a particular filetype.
(See the [list of supported sources](http://visidata.org/man#sources)).

## Documentation

* Quick reference: `F1` (or `z?`) within `vd` will open the [man page](http://visidata.org/man), which has a list of all commands and options.
* [visidata.org/docs](http://visidata.org/docs) has a complete list of links to all official documentation.

## Help and Support

For additional information, see the [support page](http://visidata.org/support).

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
