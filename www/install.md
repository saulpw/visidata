# Install VisiData

### Quick Reference

|Platform   |Package Manager|Command                                       |
|-----------+---------------+:---------------------------------------------|
|Python3.4+ |[pip3](#pip)   |`pip3 install visidata`                       |
|MacOS      |[Homebrew](#brew)|`brew install saulpw/vd/visidata`           |
|Linux (Debian/Ubuntu)|[apt](#apt)      |`apt install visidata`            |
|Python3.4+ |[conda](#conda)|`conda install --channel conda-forge visidata`|
|Python3.4+ |[github](#git) |`git clone https://github.com/saulpw/visidata.git`|

## Most flexible

The base VisiData package includes all of the loaders which are supported by the Python standard library (tsv/csv/json/sqlite/fixed-width).

The most flexible install method requires setting up a [Python3 environment](https://www.python.org/downloads/) (incl. pip3).  Doing so will allow you to install the [base VisiData](), as well as the separate requirements for any of the loaders you want to use in the future.

[pip3](#pypi)

## Preferance for the conda environment

[conda](#conda)

## For quicker installs of [base VisiData]() plus additional loaders (xls(x), http, html)

### MacOS (requires [homebrew]())

[brew](#brew)

If homebrew gives errors, see troubleshooting below, or use another install method (pip3/git/conda).

### Linux (Debian/Ubuntu, requires [apt]())

[apt](#apt)

- smoother upgrading: add our apt repo and install from there
- smaller overhead: download .deb and dpkg -i
- easy (when buster is released): apt install visidata

## Windows is not directly supported: use WSL

## Build from source

If you want to make local changes to VisiData, or use bleeding edge unreleased features (which may not always work), use git:

- git clone
- add to PATH
- add to PYTHONPATH

### To use the bleeding edge or submit pull requests:

- git checkout dev


---
####


If the one-line install commands above do not work, see below for detailed instructions, or even lower in the [Troubleshooting](#trouble) section.

## installing dependendices for additional loaders

VisiData supports [many sources](http://visidata.org/man/#loaders), but not all dependencies are installed automatically.

To install dependencies for all loaders (which might take some time and disk space), `pip3 install -r requirements.txt`.

# In-depth Installation Instructions

## #brew

See [our homebrew repository](https://github.com/saulpw/homebrew-vd) for more information.

Add the [the vd tap](https://github.com/saulpw/homebrew-vd):

~~~
brew tap saulpw/vd
~~~

To install VisiData:

~~~
brew install visidata
~~~

To update VisiData:

~~~
brew update
brew upgrade visidata
~~~


## #apt

### Linux (requires [debian's unstable repo](https://github.com/saulpw/visidata#install-via-apt))

    $ apt install visidata

See [our Debian repository](https://github.com/saulpw/deb-vd) for more information.

## #conda (requires [conda-forge](https://conda-forge.org/))

    $ conda install --channel conda-forge visidata


    $ conda install visidata

See our [our conda-forge repository](https://github.com/conda-forge/visidata-feedstock) for more information.

Add the [conda-forge](https://conda-forge.org/) channel:

~~~
$ conda config --add channels conda-forge
~~~

To install VisiData:

~~~
$ conda install visidata
~~~

To update VisiData:

~~~
conda update visidata
~~~

## #pypi

Requires Python3.4+ and [pip3](https://stackoverflow.com/questions/6587507/how-to-install-pip-with-python-3).

    $ pip3 install visidata

See [our Github repository](https://github.com/saulpw/visidata) for more information.
## pip3

First, ensure you have [Python3](https://www.python.org/downloads/) installed.

To install VisiData:

~~~
$ pip3 install visidata
~~~

To update VisiData:

~~~
pip3 install --upgrade visidata
~~~

The core pypi package comes with loaders for the most common data file formats (including csv, tsv, fixed-width text, json, sqlite, http, html and xls). Additional Python modules may be required for opening other [supported data sources](https://visidata.org/man/#loaders).

~~~
$ pip3 install module
~~~
