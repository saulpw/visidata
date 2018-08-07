# Install VisiData

This guide will cover the steps for installing VisiData and provide troubleshooting assistance.


## Quick Reference

|Platform   |Package Manager|Command                                       | Out-of-box Loaders       |
|-----------+---------------+:---------------------------------------------+--------------------------|
|Python3.4+ |[pip3](#pip3)   |`pip3 install visidata`                       | Base                     |
|Python3.4+ |[conda](#conda)|`conda install --channel conda-forge visidata`| Base, http, html, xls(x) |
|MacOS      |[Homebrew](#brew)|`brew install saulpw/vd/visidata`           | Base, http, html, xls(x)  |
|Linux (Debian/Ubuntu)|[apt](#apt)      |`apt install visidata`            | Base, http, html, xls(x)  |
|Linux (Debian/Ubuntu)|[dpkg](#dpkg)      |`dpkg -i visidata_ver_all.deb` | Base, http, html, xls(x)   |
|Windows    |[WSL](#wsl)    |Windows is not yet directly supported (use WSL)   | N/A |
|Python3.4+ |[github](#git) |`pip3 install git+https://github.com/saulpw/visidata.git@develop`| Base |

If the one-line install commands above do not work, see below for detailed instructions and troubleshooting.

## The base VisiData package

A [loader](/docs/loaders/) is a module which directs how VisiData structures and engages with a particular data source. 

Each package contains the full loader suite but differs in which loader dependencies will get installed by default. This is to avoid bloating the system for most users, who are not interested in using those features.

When we mention the base VisiData package, we are referring to the VisiData loaders whose dependencies are covered by the Python3 standard library. Currently these include the loaders for tsv, csv, fixed width text, json, and sqlite. Additionally, .zip, .gz, .bz2, and .xz files can be decompressed on the fly.

## Comprehensive installation guide

### [pip3](#pip3)

Requires:

* [Python3.4+](https://www.python.org/downloads/)
* [pip3](https://stackoverflow.com/questions/6587507/how-to-install-pip-with-python-3)

To verify that both python3 and pip3 are installed, type `python3 -m pip help` in your terminal. You should see the helpstring for pip3 in your console.

To install VisiData:

~~~
$ pip3 install visidata
~~~

To update VisiData:

~~~
$ pip3 install --upgrade visidata
~~~

VisiData supports [many sources](http://visidata.org/man/#loaders), but not all dependencies are installed automatically.

Out-of-box, you can load all file formats supported by the Python3 standard library including csv, tsv, fixed-width text, json, and sqlite. Additional Python packages may be required for opening other [supported data sources](https://visidata.org/man/#loaders).

To install any of one the dependencies:

~~~
$ pip3 install <package>
~~~

To install dependencies for all loaders (which might take some time and disk space): 

~~~
$ wget https://raw.githubusercontent.com/saulpw/visidata/stable/requirements.txt
$ pip3 install -r requirements.txt
~~~

### [conda](#conda)

Requires:

* [conda](https://conda.io/docs/user-guide/install/index.html)
* [conda-forge channel](https://conda-forge.org/)

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
$ conda update visidata
~~~

Note, that the VisiData feedstock comes preloaded with additional dependencies.

Out-of-box, you can load csv, tsv, fixed-width text, json, sqlite, http, html, .xls, and .xlsx (Microsoft Excel).

Additional Python packages will be required for opening other [supported data sources](https://visidata.org/man/#loaders). 

If these packages are included in the conda environment, they can be installed with

~~~
$ conda install <package>
~~~

### [brew](#brew)

Requires:

* MacOS
* [brew](https://brew.sh/)

Add the [the vd tap](https://github.com/saulpw/homebrew-vd):

~~~
$ brew tap saulpw/vd
~~~

To install VisiData:

~~~
$ brew install visidata
~~~

To update VisiData:

~~~
$ brew update
$ brew upgrade visidata
~~~

Note, that the VisiData formula comes preloaded with additional dependencies.

Out-of-box, you can load csv, tsv, fixed-width text, json, sqlite, http, html, .xls, and .xlsx (Microsoft Excel).

NOTE: There is no method, which is known to the package maintainer, to install additional dependencies for a brewed Python package. If anyone does know of one please, please [let us know](https://github.com/saulpw/homebrew-vd/issues/new).

### [apt](#apt)

Requires:

* Linux distribution
* `apt`

Install `apt-transport-https`, which `apt` requires to communicate with a repository using https:

~~~
$ sudo apt install apt-transport-https
~~~

Grab our public key:

~~~
$ wget https://visidata.org/devotees.gpg.key
$ sudo apt-key add devotees.gpg.key
~~~

Add our repository to `apt`'s search list:

~~~
$ sudo add-apt-repository \
    "deb [arch=amd64] https://raw.githubusercontent.com/saulpw/deb-vd/master \
    sid \
    main"
~~~

To install VisiData:

~~~
$ sudo apt update
$ sudo apt install visidata
~~~

To update VisiData:

~~~
$ sudo apt update
$ sudo apt install visidata
~~~

Note, that the VisiData `.deb` comes preloaded with additional dependencies.

Out-of-box, you can load csv, tsv, fixed-width text, json, sqlite, http, html, .xls, and .xlsx (Microsoft Excel).

### [dpkg](#dpkg)

Requires:

* Linux distribution
* [dpkg](https://help.ubuntu.com/lts/serverguide/dpkg.html.en)

dpkg allows you to manually download and install VisiData, thus bypassing the need to add the repository's index.

First, go to our [repository](https://github.com/saulpw/deb-vd/tree/master/pool/main/v/visidata) and download the preferred version of VisiData.

To install VisiData:

~~~
$ sudo dpkg -i /path/to/visidata_version_all.deb
~~~

To uninstall VisiData:

~~~
$ sudo dpkg -r visidata
~~~

Note, that the VisiData `.deb` comes preloaded with additional dependencies.

Out-of-box, you can load csv, tsv, fixed-width text, json, sqlite, http, html, .xls, and .xlsx (Microsoft Excel).

### [wsl](#wsl)

Windows is not yet directly supported. We recommend trying to use [ConEmu](https://conemu.github.io/) as your terminal on [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) (Windows Subsystem for Linux).
You can find discussion on this topic [here](https://github.com/saulpw/visidata/issues/117).

### [Build from source](#git)

If you want to use bleeding edge unreleased features (which may not always work), you can do so by installing from the development branch on git.

To install VisiData:

~~~
$ pip3 install git+https://github.com/saulpw/visidata.git@develop
~~~

See [pip3](#pip3) above for further information on loaders and dependency management.
