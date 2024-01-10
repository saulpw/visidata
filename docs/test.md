---
eleventyNavigation:
    key: Contributing Tests
    order: 99
Update: 2018-01-28
Version: VisiData 1.0
---


The `tests` folder contains functional tests in the form of `.vd` scripts, each of which records a session of VisiData commands.  These ensure that data processing works consistently and reliably.

`dev/test.sh` (run from the git root) will execute all tests.  The final sheet of each test is saved as .tsv and compared to the respective expected output checked into the `tests/golden` directory.

As of January 2024, to pass all the tests you may need to install packages: `pip install Faker h5py odfpy openpyxl pandas tomli`

To show each step of a test with a delay of 1 second between commands:

    $ bin/vd -p tests/foo.vd -w 1

To build a `.vd` file:

1. Go through all of the steps of the workflow, ending on the sheet with the final result.
2. Press `Shift+D` to view the `CommandLog Sheet`.
3. Edit the commandlog to minimize the number of commands.  Cells may be parameterized like `{foo}`, to be specified on the commandline:

    $ vd cmdlog.vd --foo=value

4. Save the cmdlog:

    Press `Shift+D` to open the `commanDlog Sheet`, and press `Ctrl+S` to save it with a `.vd` suffix.

---
