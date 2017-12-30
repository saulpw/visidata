- Date: 2017-12-27
- Version: 1.0

# How to create a loader for VisiData

The process of designing a loader is:

1. create an `open_foo` function that returns a new **Sheet**;
2. write a reload() function to load the **rows**;
3. enumerate the available **columns**;
4. define sheet-specific **commands** to interact with the rows, columns, and cells.

## 1. Create a Sheet subclass

When VisiData tries to open a source with filetype `foo`, it tries to call `open_foo(path)`, which should return an instance of `Sheet`, or raise an error. `path` is a [`Path`](/api/Path) object of some kind.

```
def open_foo(p):
    return FooSheet(p.name, source=p)

class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: foolib.Bar object
```

- The `Sheet` constructor takes the new sheet name as its first argument.
Any other keyword arguments are set as attributes on the new instance.
- Storing the `Path` as `source` is sufficient for most loaders, and so the subclass constructor can generally be omitted.
- The `rowtype` is for display purposes only.  It should be **plural**.


## 2. Load data into rows

`reload()` is called when the Sheet is first pushed, and thereafter by the user with `^R`.

Using the Sheet `source`, `reload` populates `rows`:

```
class FooSheet(Sheet):
    ...
    def reload(self):
        self.rows = []
        for r in crack_foo(self.source):
            self.rows.append(r)
```

- A `rowdef` comment should declare the **internal structure of each row**.
- `rows` must be set to a **new list object**; do **not** call `list.clear()`.

### Making the loader asynchronous

The above code will probably work just fine for smaller datasets, but a large enough dataset will cause the interface to freeze.
Fortunately, making an [async](/docs/async) loader is pretty straightforward:

1. Add `@async` decorator on the `reload` method, which causes it to be launched in a new thread.

2. Wrap the iterator with [`Progress`](/api/Progress).  This updates the **progress percentage** as it passes each element through.

3. Append each row **one at a time**.  Do not use a list comprehension; rows should become available as they are loaded.

4. Do not depend on the order of `rows` after they are added; e.g. do not reference `rows[-1]`.  The order of rows may change during an asynchronous loader.

5. Catch any `Exception`s that might be raised while handling a specific row, and add them as the row instead.  Never use a bare `except:` clause or the loader thread will not be killable.

```
class FooSheet(Sheet):
    ...
    @async
    def reload(self):
        self.rows = []
        for bar in Progress(foolib.iterfoo(self.source.open_text())):
            try:
                r = foolib.parse(bar)
            except Exception as e:
                r = e
            self.rows.append(r)
```

Test the loader with a large dataset to make sure that:

- the first rows appear immediately;
- the progress percentage is being updated;
- the loader can be cancelled (with `^C`).

## 3. Enumerate the columns

Each sheet has a unique list of `columns`. Each [`Column`](/api/Column) provides a different view into the row.


```
class FooSheet(Sheet):
    ...
    columns = [
        ColumnAttr('name'),  # foolib.Bar.name
        Column('bar', getter=lambda col,row: row.inside[2],
                      setter=lambda col,row,val: row.set_bar(val)),
        Column('baz', type=int, getter=lambda col,row: row.inside[1]*100)
    ]
```

In general, set `columns` as a class member.  If the columns aren't known until the data is being loaded, 
`reload()` should first call `columns.clear()`, and then call `addColumn(col)` for each column at the earliest opportunity.

### Column properties

Columns have a few properties, all of which are optional arguments to the constructor except for `name`:

* **`name`**: should be a valid Python identifier and unique among the column names on the sheet. (Otherwise the column cannot be used in an expression.)

* **`type`**: can be `str`, `int`, `float`, `date`, or `currency`.  By default it is `anytype`, which passes the original value through unmodified.

* **`width`**: the initial width for the column. `0` means hidden; `None` (default) means calculate on first draw.

* **`fmtstr`**: [strftime-format](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) for `date`, or a [new-style Python format string](https://docs.python.org/3/library/string.html#formatstrings) for all other types.

* **`getter(col, row)`** and/or **`setter(col, row, value)`**: functions that get or set the value for a given row.

#### The `getter` lambda

The getter is the essential functionality of a `Column`.

In general, a `Column` constructor is passed a `getter` lambda.
Columns with more complex functions should be subclasses and override `Column.calcValue` instead.

The `getter` is passed the column instance `col` and the `row`, and returns the value of the cell.
If the sheet itself is needed, it is available as `col.sheet`.

The default getter returns the entire row.

#### The `setter` lambda

The `Column` may also be given a `setter` lambda, which allows the in-memory row to be modified.
The `setter` lambda is passed the column instance `col`, the `row`, and the new `value` to be set.

In a Column subclass, `Column.setValue(self, row, value)` may be overridden instead.

By default there is no `setter`, which makes the column read-only.

### Builtin Column Helpers

There are several helpers for constructing `Column` objects:

* `ColumnAttr(colname, attrname=colname, **kwargs)` gets/sets an attribute from the row object using `getattr`/`setattr`.
  This is useful when the rows are Python objects.

* `ColumnItem(colname, itemkey=colname, **kwargs)` uses the builtin `getitem` and `setitem` on the row.
  This is useful when the rows are Python mappings or sequences, like dicts or lists.

* `SubrowColumn(origcol, subrowidx, **kwargs)` delegates to the original column with some part of the row.
This is useful for rows which are a list of references to other rows, like with joined sheets.

Recipes for a couple of recurring patterns:

- columns from a list of names: `[ColumnItem(name, i) for i, name in enumerate(colnames)]`
- columns from the first sample row, when rows are dicts: `[ColumnItem(k) for k in self.rows[0]]`

## 4. Define Sheet-specific Commands

`Command()` and `globalCommand()` have the same signature:

`Command(keystrokes, execstr, helpstr, longname)`

There is a [separate howto for Commands](/howto/dev/commands).

```
class FooSheet(Sheet):
    ...
    commands = [
        Command('b', 'cursorRow.set_bar(0)', 'reset bar to 0', 'reset-bar')
    ]
```

- Reasonably intuitive and mnemonic default keybindings should be chosen.
- The longname allows the command to be rebound by a more descriptive name, and for the command to be redefined for other contexts (so all keystrokes bound to that command will take on the new action).

## Full Example

This would be a completely functional read-only viewer for the fictional foolib.  For a more realistic example, see the [annotated viewtsv](/docs/viewtsv) or any of the [included loaders](https://github.com/saulpw/visidata/tree/stable/visidata/loaders).

```
from visidata import *

def open_foo(p):
    return FooSheet(p.name, source=p)

class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: foolib.Bar object
    columns = [
        ColumnAttr('name'),  # foolib.Bar.name
        Column('bar', getter=lambda col,row: row.inside[2],
                      setter=lambda col,row,val: row.set_bar(val)),
        Column('baz', type=int, getter=lambda col,row: row.inside[1]*100)
    ]
    commands = [
        Command('b', 'cursorRow.set_bar(0)', 'reset bar to 0', 'reset-bar')
    ]

    @async
    def reload(self):
        import foolib

        self.rows = []
        for bar in Progress(foolib.iterfoo(self.source.open_text())):
            try:
                r = foolib.parse(bar)
            except Exception as e:
                r = e
            self.rows.append(r)
```

## Extra Credit: create a saver

A full-duplex loader requires a **saver**.  The saver iterates over all `rows` and `visibleCols`, calling `getValue` or `getTypedValue`, and saves the results in the format of that filetype.

```
@async
def save_foo(sheet, fn):
    with open(fn, 'w') as fp:
        for i, row in enumerate(Progress(sheet.rows)):
            for col in sheet.visibleCols:
                foolib.write(fp, i, col.name, col.getValue(row))
```

The saver should preserve the column names and translate their types into foolib semantics, but other attributes on the Columns should generally not be saved.

---

# Building a loader for a URL schemetype

When VisiData tries to open a URL with schemetype of `foo` (i.e. starting with `foo://`), it calls `openurl_foo(urlpath, filetype)`.  `urlpath` is a [`UrlPath`](/api/Path#UrlPath) object, with attributes for each of the elements of the parsed URL.

`openurl_foo` should return a Sheet or call `error()`.
If the URL indicates a particular type of Sheet (like `magnet://`), then it should construct that Sheet itself.
If the URL is just a means to get to another filetype, then it can call `openSource` with a Path-like object that knows how to fetch the URL:

```
def openurl_foo(p, filetype=None):
    return openSource(FooPath(p.url), filetype=filetype)
```

---

