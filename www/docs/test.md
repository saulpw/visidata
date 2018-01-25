- Update: 2018-01-11
- Version: VisiData 1.0

# Contributing tests

The `tests` folder contains functional tests in the form of `.vd` scripts, each of which records a session of VisiData commands.  These ensure that data processing works consistently and reliably.

`dev/test.sh` (run from the git root) will execute all tests.  The final sheet of each test is saved as .tsv and compared to the respective expected output checked into the `tests/golden` directory.

To run a test manually:

    $ bin/vd --play tests/foo.vd --replay-wait 1

or

    $ bin/vd -p tests/foo.vd -w 1

To build a `.vd` file:

1. Go through all of the steps of the workflow, ending on the sheet with the final result.
2. Press `D` to view the `CommandLog Sheet`
3. Edit the commandlog to minimize the number of commands.  Cells may be parameterized like `{foo}`, to be specified on the commandline:

    $ vd cmdlog.vd --foo=value

4. Save the cmdlog using *one* of the following options:

    a. Press `^S` on the `CommandLog Sheet` and save it with a `.vd` suffix.

    *or*

    b. Press `^D` to save the current cmdlog to a `fn.vd` file regardless of your current context in VisiData.

---
