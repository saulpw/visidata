# VisiData v0.9 [![CircleCI](https://circleci.com/gh/saulpw/visidata/tree/stable.svg?style=svg)](https://circleci.com/gh/saulpw/visidata/tree/stable)

A curses interface for exploring and arranging tabular data

Usable via any remote shell which has Python3 installed.

A few interesting commands:

* `Shift-F` pushes a frequency analysis of the current column
* `=` creates a new column from the given Python expression (use column names to refer to their contents)
* `.` creates new columns from the match groups of the given regex

<a href="https://github.com/saulpw/visidata/blob/develop/docs/tours.rst">![VisiData silent demo](docs/img/birdsdiet_bymass.gif)]</a>

# Getting Started

## Install VisiData

### from pypi (`stable` branch)

```
$ pip3 install visidata
```

### or clone from git

```
$ git clone http://github.com/saulpw/visidata.git
$ cd visidata
$ pip install -r requirements.txt
$ python setup.py install
```

### Dependencies

- Python 3.3+
- h5py and numpy (if opening .hdf5 files)

**Remember to install the Python3 versions of these packages with e.g. `pip3`**

## Run VisiData

If installed via pip3, `vd` should launch without issue.

```
$ vd [<options>] [<inputs> ...]
```

If no inputs are given, `vd` opens the current directory.
Unknown filetypes are by default viewed with a text browser.

If installed via `git clone`, first set up some environment variables (on terminal):

```
$ export PYTHONPATH=<visidata_dir>:$PYTHONPATH
$ export PATH=<visidata_dir>/bin:$PATH
```

Further documentation is available at [readthedocs](https://visidata.readthedocs.io/).

## Contributing

VisiData was created by Saul Pwanson `<vd@saul.pw>`.

VisiData needs lots of usage and testing to help it become useful and reliable.
If you are actively using VisiData, please let me know!
Maybe there is an easy way to improve the tool for both of us.

Also please create a GitHub issue if anything doesn't appear to be working right.
If you get an unexpected error, please include the full stack trace that you get with `Ctrl-E`.

### Branch structure

Visidata has two main branches:
* [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (which should be on pypi).
* [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable).

If you wish to contribute, please fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls) against it.

A developer's guide can be found [here](http://visidata.readthedocs.io/en/stable/dev-guide).

## License

The innermost core file, `vd.py`, is licensed under the MIT license.

Other VisiData components, including the main `vd` application, addons, and other code in this repository, are licensed under GPLv3.
