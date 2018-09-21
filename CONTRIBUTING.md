### Reporting bugs

Create a GitHub issue if anything doesn't appear to be working right. If you get an unexpected error, please include the full stack trace that you get with `Ctrl-E`.
Also please attach the commandlog (saved with `Ctrl-D`) to show the steps that led to the issue.

### Contributing code

VisiData has two main branches:

- [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (what is in pypi/brew/apt).
- [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable).

To set up a visidata development environment:
* [git clone](https://git-scm.com/docs/git-clone) the [repository](https://github.com/saulpw/visidata.git).
* [git checkout](https://git-scm.com/docs/git-checkout) the `develop` branch.
* Set the [PYTHONPATH](https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH) environment variable to the toplevel visidata directory (`export PYTHONPATH=.` if running visidata from directory itself). This ensures that you are executing the code in the current checkout, instead of the global install (without needing to uninstall VisiData).

Please submit a pull request against the `develop` branch with code improvements.
