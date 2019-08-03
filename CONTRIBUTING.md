## Contributing to VisiData

### Reporting bugs

If you encounter any bugs or have any problems, please [create an issue on Github](https://github.com/saulpw/visidata/issues).

If you get an unexpected error, please include the full stack trace from `Ctrl+E` (you can save the trace with `Ctrl+S`).

Attach the commandlog (saved with `Ctrl+D`) to show the steps that led to the issue.  Please include a small subset of the source data that elicits the problem.

### Submitting code

VisiData has two main branches:

- [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (what is in pypi/brew/apt).
- [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable). All pull requests should be submitted against `develop`.

To set up a VisiData development environment:

* [git clone](https://git-scm.com/docs/git-clone) the [repository](https://github.com/saulpw/visidata.git).
* [git checkout](https://git-scm.com/docs/git-checkout) the `develop` branch.
* Set the [PYTHONPATH](https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH) environment variable to the toplevel visidata directory (`export PYTHONPATH=.` if running visidata from directory itself). This ensures that you are executing the code in the current checkout, instead of the global install (without needing to uninstall VisiData).

### Contributing money

If VisiData has saved you time and effort, please contribute to [my Patreon](https://www.patreon.com/saulpw).

### Talk about VisiData

The biggest thing you can do to help VisiData is to spread the word.
Write blogposts, post tweets, mention it on podcasts.
Be specific about how you use it and what you love about it.

# Credits

## Maintainers

- [Saul Pwanson](http://saul.pw) ([@saulpw](https://github.com/saulpw)) conceived and developed VisiData
- [Anja Kefala](http://kefala.info) ([@anjakefala](https://github.com/anjakefala)) maintains the documentation and packages for all platforms.

## Patrons

Thanks to the following people who have contributed financial support via [Patreon](https://www.patreon.com/saulpw).

- Mike E

## Contributors

Many thanks also to the following people for their contributions to VisiData:

- [azag0](https://github.com/azag0)
- [brannerchinese](https://github.com/brannerchinese)
- [chocolateboy](https://github.com/chocolateboy)
- [deinspanjer](https://github.com/@deinspanjer)
- [eliasdorneles](https://github.com/eliasdorneles)
- [jamesroutley](https://github.com/jamesroutley)
- [khughitt](https://github.com/khughitt)
- [jkiely](https://github.com/jkiely)
- [jpgrayson](https://github.com/jpgrayson)
- [jsvine](https://github.com/jsvine)
- [layertwo](https://github.com/layertwo)
- [repjarms](https://github.com/repjarms)
- [robcarrington](https://github.com/robcarrington)
- [scl17](https://github.com/scl17)
- [ssiegel](https://github.com/ssiegel)
- [trentgill](https://github.com/trentgill)
- [vbrown608](https://github.com/vbrown608)
- [wavexx](https://github.com/wavexx)
- [zormit](https://github.com/zormit)

## Open Source License

VisiData is an open-source tool that can be installed and used for free (under the terms of the [GPL3](https://www.gnu.org/licenses/gpl-3.0.en.html)).

The core VisiData utility and rendering library will always be both free and libre.
