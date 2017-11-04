## Contributing

VisiData was written for those of us on the edge, with one foot necessarily in the old world while we gain our footing in the new world.  I am always looking for feedback and contributions to help make the tool more useful and reliable.

### Feature requests or enhancements

If you use VisiData, I would love it if you reached out to me to discuss some of your common workflows and needs. This helps me better prioritize which functionality to add. Send me a [screencast](http://asciinema.org), or some sample data along with your desired output.  There is probably a way to tweak VisiData to get the job done even more to your liking.  Feature requests should be made as posts on [reddit/visidata](http://reddit.com/r/visidata), or by emailing me at [saul@visidata.org](mailto:saul@visidata.org).

### Filing issues or support

Create a GitHub issue if anything doesn't appear to be working right. If you get an unexpected error, please include the full stack trace that you get with `^E`. If you are struggling with learning how to use the tool, or are unsure how something works, please also file an issue or write a comment in any of our community spaces. In addition to wanting to help users get the most out of the tool, this helps me gauge the holes in our documentation.

### Code contributions

VisiData has two main branches:
* [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (which should be on pypi).
* [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable).

If you wish to contribute code, please fork from [develop](https://github.com/saulpw/visidata/tree/develop) and submit a [pull request](https://github.com/saulpw/visidata/pulls) against it.

A guide to VisiData's architecture and internals can be found [here](http://visidata.org/design).

In addition, the innermost core file, `vdtui.py`, is a single-file stand-alone library that provides a solid framework for building text user interface apps. It is distributed under the MIT free software license, and freely available for inclusion in other projects. If you develop any application using it, I would love to see it!

### Contributing to test development

The `tests` folder contains functional tests in the form of `.vd` scripts, each of which records a session of VisiData commands.  These ensure that data processing works consistently and reliably.

`test.sh` (run from the git root) will execute all tests.  The final sheet of each test is saved as .tsv and compared to the respective expected output checked into the `tests/golden` directory.

To run a test manually:

```
       $ bin/vd --play tests/foo.vd --delay 1
    or $ bin/vd -p tests/foo.vd -d 1
```

To build a `.vd` file:

1. Go through all of the steps of the workflow, ending on the sheet with the final result.
2. Press `Shift-D` to view the commandlog.
3. Edit the commandlog to minimize the number of commands.  Cells may be parameterized like `{foo}`, to be specified on the commandline:

    $ vd cmdlog.vd --foo=value  

4. Press `^S` to save the commandlog to a `.vd` file.

As a shortcut, `^D` will save the current commandlog, by default to the next non-existing 'cmdlog-#.vd'

### Contributing to documentation

If you notice a `globalCommand()` or `Command()` which does not have an entry in the VisiData manpage, please file an issue. In addition, if something is not clear (and in fact, is confusing) let us know so that we can better improve on the documentation.

If you would like to contribute by building an asciicast, the process is shown at [visidata.org/test/meta](http://visidata.org/test/meta).

If you would like to take a plunge into our mandocs, they are located in `visidata/man` and are divided based on the source of the functionality. `vdtui` keystrokes are split off based on functionality, while all of the rest of VisiData's keystrokes are in `vd-keystrokes.inc`. Please do not directly edit `vd.1`, as it is built automatically by stitching together the other files.

### Community

If you want to chat about VisiData, learn how to use it to maximum effect, or discuss possibilities in the VisiData multiverse, here is where I and other contributors and users can be reached:

- [r/visidata](http://reddit.com/r/visidata) on reddit
- #visidata on [freenode IRC](https://webchat.freenode.net)
- [saul@visidata.org](mailto:saul@visidata.org) via email
