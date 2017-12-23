# How to create a loader for VisiData


The process of designing a loader is:

1. Create a Sheet subclass;
2. Collect the rows from the sources in reload();
3. Enumerate the available columns;
4. Create sheet-specific commands to interact with the rows, columns, and cells.

## 1. Create a Sheet subclass

When VisiData tries to open a source with filetype `foo`, it tries to call `open_foo(path)`.  `path` is a [Path](/api/Path) object of some kind.

Sheet constructors should take a name as their first parameter, and pass their `**kwargs` along to the [Sheet superclass](/api/Sheet), which will use some of them and set the rest as attributes on the new instance.

Besides the name, the main thing the constructor has to do is set its `source` for `reload()`:

```
def open_foo(p):
    return FooSheet(p.name, source=p)

class FooSheet(Sheet):
    def __init__(self, name, **kwargs):
        super().__init__(self, name, **kwargs)
        self.gpg = generate_key()
```

## 2. Collect data into rows

`reload()` is called when the Sheet is first pushed, and thereafter by the user with `^R`.

Using the Sheet `source`, `reload` populates `rows`:

```
class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: Foo
    # If the constructor does not have to do anything special, it can be omitted entirely.
    def reload(self):
        self.rows = []
        for r in crack_foo(self.source):
            self.addRow(r)
```

The `rowtype` is for display purposes only.  It should be plural.
The expected internal structure of the rows on this sheet always be declared in a comment with the searchable tag `rowdef`.

### making it async

1. Add `@async` decorator on `reload`.  This causes the method to be launched in a new thread.

2. Append each row one at a time.
  - Use `addRow` in general, even though it merely calls `self.rows.append(r)`.
  - Do not use a list comprehension, so that rows will be available before everything is loaded.
  - Do not assume the order of the rows will be the allocate rows and then fill them in.  The user may change the order of the rows 

3. Wrap the iterator with [Progress](/api/Progress).  This updates the progress percentage as it passes each element through.

```
class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: Foo
    @async
    def reload(self):
        self.rows = []
        for r in Progress(crack_foo(self.source)):
            self.addRow(r)
```

## 3. Enumerate the columns

Each `Column` provides a different view into the row.

In general, set the `columns` class member to a list of `Column`s:

```
class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: Foo
    columns = [
        ColumnAttr('name'),
        Column('bar', getter=lambda col,row: row.inside[2],
                      setter=lambda col,row,val: row.set_bar(val)),
        Column('baz', type=int, getter=lambda col,row: row.inside[1]*100)
    ]
    ...
```

If the columns aren't known beforehand (e.g. they have to be discovered while parsing the data), then they can be added with `addColumn` during `reload()`.
If this mechanism is used, reload has to clear the existing columns list first, or every reload will add another full set of columns.

### Column properties

Columns have a few properties, all optional in the constructor except for `name`:

* **`name`**: should be a valid Python identifier and unique among the column names on the sheet.  Otherwise the column cannot be used in an expression.

* **`type`**: values can be `str` (`~`), `int` (`#`), `float` (`%`), `date` (`@`), `currency` (`$`).  It can also be `anytype`, which passes the original value through unmodified.

* **`width`**: specifies the initial width for the column; `0` means hidden, `None` (default) means calculate on first draw.

* **`fmtstr`**: format string for use with `type`.  May be [strftime-format]() for `date`, or `new-style format` for other types.

#### `getter`

The `Column` constructor is usually passed a `getter` lambda, at least.
For complex getters, a Column subclass can override the base method `Column.calcValue` instead.
The getter is the essential functionality of a `Column`.

The `getter` lambda is passed the column instance (`col`) and the `row`, and returns the value of the cell.
The sheet may be gotten from `col.sheet`; `row in col.sheet.rows` should always be true.

The default getter returns the entire row.


#### `setter`

The `Column` may also be given a `setter` lambda, which allows a row to be modified (e.g. by a command that uses the `Sheet.editCell` method).
The `setter` lambda is passed the column instance (`col`), the `row`, and the new `value` to be set.

By default there is no `setter`, so the column is read-only.

In a Column subclass, `Column.setValue(self, row, value)` may be overridden instead.

### Builtin Columns

There are several helpers for constructing `Column` objects:

* `ColumnAttr(attrname, **kwargs)` gets/sets an attribute from the row object using `getattr`/`setattr`.
  This is useful when the rows are Python objects.

* `ColumnItem(colname, itemkey, **kwargs)` uses the builtin `getitem` and `setitem` on the row.
  This is useful when the rows are Python mappings or sequences, like dicts, lists, and tuples.

* `SubrowColumn(origcol, subrowidx, **kwargs)` delegates to the original column with some part of the row.
This is useful for rows which are a list of references to other rows, like with joined sheets.

A couple recurring patterns:

- columns from a list of names: `[ColumnItem(name, i) for i, name in enumerate(colnames)]`
- columns from the first sample row, when rows are dicts: `[ColumnItem(k) for k in self.rows[0]]`

## 4. Add Sheet-specific Commands

```
class FooSheet(Sheet):
    rowtype = 'foobits'  # rowdef: Foo
    commands = [
        Command('b', 'cursorRow.set_bar(0)', 'reset bar to 0', 'reset-bar')
    ]
```

A reasonably intuitive and mnemonic default keybinding should be chosen.
The [`execstr` and `helpstr`](/api/Command)
The longname allows the command to be rebound by a more descriptive name, and for the command to be redefined for other contexts (so all keys bound to that command will be redefined also).

# Building a loader for a URL schemetype

When VisiData tries to open a URL with schemetype of `foo` (i.e. starting with `foo://`), it calls `openurl_foo(urlpath, filetype)`.  `urlpath` is a [UrlPath](/api/Path#UrlPath) object, with attributes for each of the elements of the parsed URL.

`openurl_foo` should return a Sheet or call `error()`.
If the URL indicates a particular type of Sheet (like `magnet://`), then it should construct that Sheet itself.
If the URL is just a means to get to another filetype, then it can call `openSource` with a Path-like object that knows how to fetch the URL:

```
def openurl_foo(p, filetype=None):
    return openSource(FooPath(p.url), filetype=filetype)
```

# Tests

- `^R` reload
- try with large dataset, make sure it stays responsive and updates progress
