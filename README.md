# VisiData v0.59

A curses interface for exploring and arranging tabular data

Usable via any remote shell which has Python3 installed.

![VisiData silent demo](docs/img/screenshot.gif "VisiData Screenshot")


# Getting Started

## Install VisiData

### from pypi (`stable` branch)

```
$ pip3 install visidata
```

### or clone from git

```
$ git clone http://github.com/saulpw/visidata.git
```

### Dependencies

- Python 3.3
- python3-dateutil (if converting string column to datetime)
- openpyxl (if opening .xlsx files)
- h5py and numpy (if opening .hdf5 files)
- google-api-python-client (if opening Google Sheets; must [also set up OAuth credentials](https://developers.google.com/sheets/quickstart/python )

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
$ export PYTHONPATH=$PYTHONPATH:<visidata_dir>
$ export PATH=$PATH:<visidata_dir>/bin
```

Further documentation is available at [readthedocs](https://visidata.readthedocs.io/).

## Contributing

VisiData was created by Saul Pwanson `<vd@saul.pw>`.

VisiData needs lots of usage and testing to help it become useful and reliable.
If you are actively using VisiData, please let me know!
Maybe there is an easy way to improve the tool for both of us.

Also please create a GitHub issue if anything doesn't appear to be working right.
If you get an unexpected error, please include the full stack trace that you get with `^E`.

### Branch structure

Visidata has two main branches:
* [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of visidata.
* [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of visidata (which will eventually be merged to stable).

If you wish to contribute, please fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls) against it.

A developer's guide can be found [here](http://visidata.readthedocs.io/en/stable/dev-guide).

## License

VisiData is licensed under GPLv3.
