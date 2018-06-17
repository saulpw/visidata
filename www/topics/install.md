# The base VisiData package

A [loader](/docs/loaders/) is a module which directs how VisiData loads and engages with a particular data source. 

Each package contains the full loader suite but differs in which loader dependencies will get installed by default. This is to avoid bloating the system for most users, who are not interested in using those features.

When we mention the base VisiData package, we are referring to the VisiData loaders whose dependencies are covered by the Python3 standard library. Currently these include the loaders for tsv, csv, fixed width text, json, and sqlite. Additionally, .zip, .gz, .bz2, and .xz files can be decompressed on the fly.

# Overview of installation decision tree

## Dependency flexibility

The most flexible installation methods require setting up a Python3 environment either through [pip3](#pip3) (including pip3) or [conda](#conda). Doing so will allow you to configure a minimal install containing only the requirements for the loaders you wish to use in the future.

Besides providing flexibility to users that are conscious of install bloat, this method is especially recommended for those interested in the loaders whose dependencies are not included by default in [brew]() or [apt](). Both of those package managers are not smoothly pliable to installing bonus optional dependencies.

### Include potential list of libraries which are not available in conda here

## For quicker installs of base VisiData, plus additional loaders (xls(x), http, html)

## Why homebrew or apt?
* most users relate to visidata as an application, not a library
* smoother installation and usage experience for users not comfortable with Python
* reasonable default dependencies for most common use-cases
* guaranteed installation of manpage

[apt](#apt)
- smoother upgrading: add our apt repo and install from there
- smaller overhead: download .deb and dpkg -i
- easy (when buster is released): apt install visidata
