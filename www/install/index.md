# Installation

There are three options for installing visidata:

- [pip3](/install#pip3) for users who wish to import visidata into their own code or wish to integrate it into a python virtual environment
- [brew](/install#brew) on MacOS for reliable installation of application components (such as the manpage)
- [apt](/install#apt) on Linux distributions

## Install via pip3

This is the best installation method for users who wish to take advantage of VisiData in their own code, or integrate it into a Python3 virtual environment.

To install VisiData, with loaders for the most common data file formats (including csv, tsv, fixed-width text, json, sqlite, http, html and xls):

```
$ pip3 install visidata
```

To install VisiData, plus external dependencies for all available loaders:

```
pip3 install "visidata[full]"
```

## Install via brew

Ideal for MacOS users who primarily want to engage with VisiData as an application. This is currently the most reliable way to install VisiData's manpage on MacOS.

```
brew install saulpw/vd/visidata
```

Further instructions available [here](https://github.com/saulpw/homebrew-vd).

## Install via apt

Packaged for Linux users who do not wish to wrangle with PyPi or python3-pip.

Currently, VisiData is undergoing review for integration into the main Debian repository. Until then it is available in our [Debian repo](https://github.com/saulpw/deb-vd).

Grab our public key

```
wget http://visidata.org/devotees.gpg.key
apt-key add devotees.gpg.key
```

Add our repository to apt's search list

```
sudo apt-get install apt-transport-https
sudo vim /etc/apt/sources.list
    deb[arch=amd64] https://raw.githubusercontent.com/saulpw/deb-vd/master sid main
sudo apt-get update
```

You can then install VisiData by typing:

```
sudo apt-get install visidata
```

Further instructions are available [here](https://github.com/saulpw/deb-vd).
