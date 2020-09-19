# Loaders

## Loader Checklist

1. [] `open_foo` boilerplate
2. [] FooSheet rowdef and reload/iterload
3. [] FooSheet.columns
4. [] Any FooSheet.addCommand(...) at the bottom of the .py
5. [] Any vd.option() at the top of the .py

## Hello Loader

The most basic loader reads in a text file:

### Step 1.  `open_` filetype boilerplate

~~~
def open_readme(p):
    return ReadmeSheet(p.name, source=p)
~~~

This is used for filetype `readme`, which is used for files with extension `.readme`, or when specified manually with the `filetype` option.

The `open_<filetype>` function almost always looks exactly like this, with only the type of Sheet changed.
Of course, an existing [sheet type]() can be used.

`p` is a [`visidata.Path`]().

The actual loading happens in the Sheet:

## Step 2.  Create a Sheet subclass

~~~
class ReadmeSheet(TableSheet):
    rowtype = 'lines'   # rowdef: [str]
~~~

- TableSheet (also just `Sheet`) is the basic tabular sheet of rows and columns.
Most loader sheets will inherit from TableSheet, but some might inherit from more specialized sheets if they share functionality, or from `BaseSheet` if they are not tabular (like the `Canvas`).

- The `rowtype` member is only displayed on the [right-hand status]().
It should be **plural**.
If not given, it is "`rows`".
It's helpful to give the user an subconscious check of the kind of sheet being shown.

- The `rowdef` should be given for all loaders, even though it is only a comment.
It specifies the expected Pythonic structure of the rows on this sheet.
This is important because nearly every other component of the sheet depends on this structure.

## Step 2. Load data into rows, and yield them one-by-one

`reload()` is called when the Sheet is first pushed, and thereafter by the user with `^R`.
The default `TableSheet.reload()` iterates through the rows returned by `iterload`, and takes care of a few common commonalities (like running async and resetting the `rows` member),
Each loader then defines an `iterload`, which uses the Sheet `source` to populate and then yield each row one-by-one.

~~~
class ReadmeSheet(TableSheet):
    rowtype = 'lines'   # rowdef: [str]

    def iterload(self):
        for line in self.source:
            yield [line]
~~~

- `str` is not actually a valid rowdef.
   - Each row must have a unique `rowid`, which by default is the Python `id()` of the row.
Because Python interns common strings, strings with the same value will have the same rowid.
This breaks a lot of features.
   - Also, as an immutable type, it would be annoyingly uneditable.
   - So it's wrapped it in a Python `list`, which is guaranteed to be mutable and unique.

- `source` is a Path; the same as the source kwarg given in `open_readme`.
In fact, any kwarg passed to a Sheet constructor will be stored on the sheet in a member of the same name.

- [`visidata.Path`] objects are Path-like but have some additional features, like being iterable (yielding their contents one line at a time).
   - This case is optimized to read the file a small amount at a time.
   Do **not** use e.g. `for line in p.read().splitlines()`, as that will read the entire file before returning the first line.
   Always consider if your code will work well with 1GB of data.
   Ideally test with a too-large amount of data to make sure it degrades gracefully.

- If the loader requires a third-party library, import it inside iterload() or reload() (or `open_` if necessary).
Do not import at the toplevel or `vd` will fail to start if the library is not installed.

By default, a Sheet has one Column which just displays a string representation of the row.
So the above example is a good starting point for any loader; just get the rows however they come most easily from the source, and launch vd with a sample dataset.
Then use `Ctrl+Y` to explore the row as a Python object to find what properties you want to see.

### reload()

For more control over the whole loading process, BaseSheet.reload() can be overridden instead of using iterload():

~~~
    @asyncthread
    def reload(self):
        self.rows = []
        for line in self.source:
            self.addRow([line])
~~~

- `@asyncthread` launches the decorated function in its own thread.
- `rows` must be reset to a new object.  **Never call `rows.clear()`**.
- In a loader, always add rows using [`addRow()`](), and columns using [`addColumn()`]().

### Supporting asynchronous loaders

Large enough datasets will cause the interface to freeze.
Fortunately, the stock `reload` and the `iterload` structure results in an [async](/docs/async) loader on default.
Since rows are yielded **one at a time**, they become available as they are loaded, and `reload` itself is decorated with an `@asyncthread`, which causes it to be launched in a new thread.

Further things to take into account:
- All row iterators should be wrapped with [`Progress`](/docs/async#Progress).  This updates the **progress percentage** as it passes each element through.
- Do not depend on the order of `rows` after they are added; e.g. do not reference `rows[-1]`.  The order of rows may change during an asynchronous loader.
- Catch any `Exception`s that might be raised while handling a specific row, and add them as the row instead.  If `Exception` handling is missing within iterload, rows will stop loading upon hitting an `Exception`. Never use a bare `except:` clause or the
 loader thread will not be cancelable with `Ctrl+C`.

#### Progress and Exception example

~~~
    class FooSheet(Sheet):
        ...
        def iterload(self):
            for bar in Progress(foolib.iterfoo(self.source.open_text())):
                try:
                    r = foolib.parse(bar)
                except Exception as e:
                    r = e
                yield r
~~~

Test the loader with a large dataset to make sure that:

- the first rows appear immediately;
- the progress percentage is being updated;
- the loader can be cancelled (with `Ctrl+C`).

## 3. Enumerate the Columns

Each sheet has a unique list of `columns`. Each `Column` provides a different view into the row.

~~~
    class FooSheet(Sheet):
        rowtype = 'foobits'  # rowdef: foolib.Bar object

        columns = [
            ColumnAttr('name'),  # foolib.Bar.name
            Column('bar', getter=lambda col,row: row.inside[2],
                          setter=lambda col,row,val: row.set_bar(val)),
            Column('baz', type=int, getter=lambda col,row: row.inside[1]*100)
        ]
~~~

In general, set `columns` as a class member.  If the columns aren't known until the data is being loaded,
**Sheet**'s `__init__()` will check if `self.columns` was set and add each column at the earliest opportunity.

A few snippets:

- columns from a list of names: `[ColumnItem(name, i) for i, name in enumerate(colnames)]`
- columns from the first row, when rows are dicts: `[ColumnItem(k) for k in self.rows[0]]`


### Column properties

Columns have a few properties, all except `name` are **optional** arguments to the constructor:

* **`name`**: should be a valid Python identifier and unique among the column names on the sheet. (Otherwise the column cannot be used in an expression.)

* **`type`**: can be `str`, `int`, `float`, `date`, or `currency`.  By default it is `anytype`, which passes the original value through unmodified.

* **`width`**: the initial width for the column. `0` means hidden; `None` (default) means calculate on first draw.

Column getters can be any function, but many loaders for are satisfied with a static list of ItemColumn (for a value in dict and list rowdefs) and/or AttrColumn (for a member or property directly on the row object).
This is dependent on the loader function; some loaders may prefer to do less parsing to load faster, and then the Columns need to be correspondingly more complicated.

See the [Columns section]() for a complete API.

### Passthrough options

Loaders which use a Python library (internal or external) are encouraged to pass all options to it through the `options("foo_")`.  For modules like csv which expose them as kwargs to some function or constructor, this is very easy:

~~~
    rdr = csv.reader(fp, **csvoptions())
~~~

### Full Example

This would be a completely functional read-only viewer for the fictional foolib.
For a more realistic example, see the [annotated viewtsv](/docs/viewtsv) or any of the [included loaders](https://github.com/saulpw/visidata/tree/stable/visidata/loaders).

~~~
    from visidata import *

    vd.option('foo_scale', 100, 'amount to scale baz')


    class FooSheet(Sheet):
        rowtype = 'foobits'  # rowdef: foolib.Bar object
        columns = [
            ColumnAttr('name'),  # foolib.Bar.name
            Column('bar', getter=lambda col,row: row.inside[2],
                          setter=lambda col,row,val: row.set_bar(val)),
            Column('baz', type=int, getter=lambda col,row: row.inside[1]*options.foo_scale)
        ]

        def iterload(self):
            import foolib

            for bar in Progress(foolib.iterfoo(self.source.open_text())):
                try:
                    r = foolib.parse(bar, **options.getall('foo_'))
                except Exception as e:
                    r = e
                yield r


    FooSheet.addCommand(ALT+'b', 'reset-bar', 'cursorRow.set_bar(0)')
~~~

## Savers

A full-duplex loader requires a **saver**.  The saver iterates over all `rows` and `visibleCols`, calling `getValue`, `getDisplayValue` or `getTypedValue`, and saves the results in the format of that filetype. Savers should be decorated with `@VisiData.ap
i` in order to make them available through the `vd` object's scope.

~~~
    @VisiData.api
    def save_foo(vd, path, sheet):
        with path.open_text(mode='w') as fp:
            for i, row in enumerate(Progress(sheet.rows)):
                for col in sheet.visibleCols:
                    foolib.write(fp, i, col.name, col.getValue(row))
~~~

The saver should preserve the column names and translate their types into foolib semantics, but other attributes on the Columns should generally not be saved.


## Building a loader for a URL schemetype

When VisiData tries to open a URL with schemetype of `foo` (i.e. starting with `foo://`), it calls `openurl_foo(urlpath, filetype)`.  `urlpath` is a `UrlPath` object, with attributes for each of the elements of the parsed URL.

`openurl_foo` should return a Sheet or call `error()`.
If the URL indicates a particular type of Sheet (like `magnet://`), then it should construct that Sheet itself.
If the URL is just a means to get to another filetype, then it can call `openSource` with a Path-like object that knows how to fetch the URL:

~~~
    def openurl_foo(p, filetype=None):
        return openSource(FooPath(p.url), filetype=filetype)
~~~
