
# VisiData v2.10.2 [![twitter @VisiData][1.1]][1] [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable) [![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/saulpw/visidata)

A terminal interface for exploring and arranging tabular data.

![Frequency table](http://visidata.org/freq-move-row.gif)

VisiData supports tsv, csv, sqlite, json, xlsx (Excel), hdf5, and [many other formats](https://visidata.org/formats).

## Platform requirements

- Linux, OS/X, or Windows (with WSL)
- Python 3.6+
- additional Python modules are required for certain formats and sources

## Install

To install the latest release from PyPi:

    pip3 install visidata

To install the cutting edge `develop` branch (no warranty expressed or implied):

    pip3 install git+https://github.com/saulpw/visidata.git@develop

See [visidata.org/install](https://visidata.org/install) for detailed instructions for all available platforms and package managers.

### Usage

    $ vd <input>
    $ <command> | vd

Press `Ctrl+Q` to quit at any time.

Hundreds of other commands and options are also available; see the documentation.

### Documentation

* [VisiData documentation](https://visidata.org/docs)
* [Plugin Author's Guide and API Reference](https://visidata.org/docs/api)
* [Quick reference](https://visidata.org/man) (available within `vd` with `Ctrl+H`), which has a list of commands and options.
* [Intro to VisiData Tutorial](https://jsvine.github.io/intro-to-visidata/) by [Jeremy Singer-Vine](https://www.jsvine.com/)

### Help and Support

If you have a question, issue, or suggestion regarding VisiData, please [create an issue on Github](https://github.com/saulpw/visidata/issues) or chat with us at #visidata on [irc.libera.chat](https://libera.chat/).

If you use VisiData regularly, please [support me on Patreon](https://www.patreon.com/saulpw)!

## License

Code in the `stable` branch of this repository, including the main `vd` application, loaders, and plugins, is available for use and redistribution under GPLv3.

## Credits

VisiData is conceived and developed by Saul Pwanson `<vd@saul.pw>`.

Anja Kefala `<anja.kefala@gmail.com>` maintains the documentation and packages for all platforms.

Many thanks to numerous other [contributors](https://visidata.org/credits/), and to those wonderful users who provide feedback, for helping to make VisiData the awesome tool that it is.

[1.1]: http://i.imgur.com/tXSoThF.png
[1]: http://www.twitter.com/VisiData

<!-- Please don't remove this: Grab your social icons from https://github.com/carlsednaoui/gitsocial -->
