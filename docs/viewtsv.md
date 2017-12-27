# viewtsv

Date: 2017-12-27  Version: 1.0

[viewtsv](https://github.com/saulpw/visidata/blob/stable/bin/viewtsv)
is a great example of a minimal [vdtui](https://github.com/saulpw/visidata/blob/stable/visidata/vdtui.py) application.  This is an extremely functional utility in 25 lines of code.  Here it is in its entirety, with line by line annotations:

```
#!/usr/bin/env python3
```

VisiData 1.0 requires Python 3.4+.

```
import sys
import vdtui
```

Copy `vdtui.py` into your application verbatim.  It's freely usable under the MIT license, and then you can just import it like this and use it without adding any external dependencies to your project.

```
class TsvSheet(vdtui.Sheet):
    rowtype = 'rows'  # rowdef: tuple of values
```

All tabular data sheets inherit from `Sheet`.  The rowtype is displayed in the lower right of the status line and provides a context for the user. The [rowdef](https://github.com/saulpw/visidata/blob/2673ae47f334e9e2b1fbd1afc4a28185440a66f7/visidata/loaders/postgres.py#L55) is a useful comment for every Sheet which outlines its initial structure.

```
    columns = [vdtui.ColumnItem('tsv', 0)]
```

An initial column.  Generally the class-level `columns` is set to the actual columns of the sheet, but in this case, the columns aren't known until the source is loaded.
\(See the `reload()` function below where they are set with the contents of the source.\)  This line is not strictly necessary but makes loading feel a bit more responsive.


```
    @vdtui.async
```

@[async](/docs/async) marks the function to spawn a new thread whenever it is called.

```
    def reload(self):
```

The [`reload()`](/howto/dev/loaders) function collects data from the source and puts it into `rows`.  It's called once automatically when first pushed, and manually with `^R`.

```
        self.rows = []
```

`rows` is a list of Python objects.  The row definition ('rowdef') for the TsvSheet is a tuple of values, with each position corresponding to one column.

```
        with open(self.source, encoding=vdtui.options.encoding) as fp:
```
`source` is the filename, which has been passed to the constructor (see the last line with `run()`).

```
            for line in fp:
                line = line[:-1]
                if line:
                    self.rows.append(line.split('\t'))
```

For each line, strip the included newline character, and filter out any blank lines.  Add each split tuple to `rows`.

```
        self.columns = [
             vdtui.ColumnItem(colname, i)
                 for i, colname in enumerate(self.rows[0])
        ]
```
The actual columns are set from the first (header) row.
`ColumnItem` is a builtin, which creates a column to use getitem/setitem with the given key/index.
```
        self.rows = self.rows[1:]
```
The header row is removed from the list of rows.  (Column names are displayed on the first row anyway).

```
vdtui.run(*(TsvSheet(fn, source=fn) for fn in sys.argv[1:]))
```
`run(*sheets)` is the toplevel entry point for vdtui.



---

