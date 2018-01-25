
## Sheets

Every displayed screen is an instance of `Sheet`, which manages its [rows](#reload), [columns](/column), [cursor](#cursor), and [display](#display).

These will each be described in detail below.  [See the API reference](/api/Sheet) for the full API.

### Sheet Example Code

Here is the complete code for a simple DictSheet.

    # rowdef: source key
    class DictSheet(Sheet):
        rowtype = 'items'
        columns = [
            Column('key'),
            Column('value', getter=lambda col,row: col.sheet.source[row])
        ]
        def reload(self):
            self.rows = list(self.source.keys())

    globalCommand('1', 'vd.push(DictSheet("globals", source=globals()))', 'push globals dict')

If this code is [loaded](/design/addons), pressing `1` will push a fresh instance of `DictSheet`, showing each key in the `globals()` dict with its corresponding value.

### The Essential Steps to Create a Sheet

#### 1. Gather the name and sources for the constructor

##### `Sheet(name, **kwargs)`

The constructor of a sheet should always take a `name` (str).  Additional Sheet parameters are passed via `kwargs`, and will be made available as attributes on the Sheet instance.

The `source` of a Sheet is usually passed into the constructor.  For a sheet loaded from a file, the source will be a [`Path`](/api/Path) object.

Derived sheets will have other `Sheet` instances as their `source`.

But really, the source needed is dependent on that Sheet's `reload()` which collects the data.

#### 2. Collect `rows` in `Sheet.reload()`

The `reload()` member on a Sheet must populate the 

#### 3. Enumerate the `columns`

Columns can either be specified in the class scope (as per the example), populated in the constructor (if dependent on the sources), or if necessary, populated by reload if dependent on the data itself.

#### 4. Instantiate the sheet in a `globalCommand`

#### 5. Enjoy your new sheet!

### viewport

Here is a diagram of the screen layout:

[img]

#### row layout

- `topRowIndex` index of row just below header row
- `nVisibleRows`: simply based on terminal height, the number of rows that can be displayed.
- `visibleRows`: the contiguous slice of `rows` which is visible onscreen

Column layout is more involved:

1. the first `nKeys` columns are 'key' columns, which are pinned to the left and always visible.
2. columns are variable width.
3. if a column's width is 0, it is not visible (`hidden`).

Invisible columns make it more difficult to move the column cursor sensibly.  So Sheet has a computed property `visibleCols`, which is the better choice for most tasks.  `hidden` columns still exist (go to the `C`olumns sheet to unhide them), but they should remain invisible in most cases.

- `visibleCols`: (O(ncols), cached between frames): list of all non-hidden columns
- `leftVisibleColIndex` is the first non-key column on the left.
- `rightVisibleColIndex` (computed by `Sheet.calcColLayout()`, assignment will be ignored)

### the Row and Column Cursor [name=cursor]

The primary (settable) row cursor is `cursorRowIndex`, which is an index into `rows`.

The primary (settable) column cursor is `cursorVisibleColIndex`, which is an index into `visibleCols`.

The other cursor properties are computed:

- `cursorColIndex` (O(ncols)); index into .columns
- `cursorRow`: equivalent to `rows[cursorRowIndex]`
- `cursorCol`: equivalent to `columns[cursorColIndex]` (and visibleCols[cursorVisibleColIndex])

#### the value at the cursor (the current cell)

- `cursorCell`:
- `

### DisplayWrapper [name=display]
