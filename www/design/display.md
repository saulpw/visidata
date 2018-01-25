# The Design of VisiData: Display Engine

## Sheet

Every displayed screen is an instance of the `Sheet` class, which has several members:

- `rows`
- `columns`
- `topRowIndex` index of row just below header row
- `cursorRowIndex`
- `cursorColIndex` (computed, O(ncols)); index into .columns

Computed properties:

- `cursorRow`: rows[cursorRowIndex]
- `cursorCol`: columns[cursorColIndex] (equivalent to visibleCols[cursorVisibleColIndex])
- `nVisibleRows`: simply based on terminal height, the exact number of rows that can be displayed.
- `visibleRows`: slice of onscreen rows; 'visible' has different meaning than visibleCols
- `visibleCols`: (O(ncols), cached between frames): list of all non-hidden columns
- `leftVisibleColIndex` is the first non-key column on the left.
- `rightVisibleColIndex` (computed by `Sheet.calcColLayout()`, assignments ignored)
- `cursorVisibleColIndex`


- Sheet.rows
  - populated by `Sheet.reload()`.
  - must be a randomly addressable sequence
  - can only be reordered if rows is mutable
  - rows is usually a list.  [future] could be other types, would go terabyte easily then

- Sheet.columns
  - populated by init or copied from subclass
  - can be populated by reload if data dependent


Any `*VisibleCol*` property is an index into `visibleCols`.

Originally, cursorColIndex was the canonical column position, but this made many things more complicated than necessary.
In particular, this allowed the cursor to be on a hidden column, which had to be considered for many column commands.

The canonical column position is now cursorVisibleColIndex, so the cursor is always on a non-hidden column by design.
cursorColIndex (and others) must now be computed, which can be expensive if there are many columns, but these computed properties can be cached, and the resulting code is cleaner.

## Column

**The fundamental abstraction of VisiData, is that every Column is essentially a function of the row.**

A VisiData column, in essence, is simply a function which takes a row and returns a value.

The Column object has other associated niceties (any of which may be passed as kwargs to init)
- name
  set with `^`
- getter(r): the main function called by Column.calcValue()
- setter(sheet,col,row,val): the function called by Column.setValue()
  set with 'e'
  'zd' or 'Del' sets to None
- width: '0' if hidden; `None` if should be auto-set on first visibility (default)
   adjusted by '-' and '\_'
- [type](/design/types): int, str, float, date, currency, anytype (default)
   set with ~@#$% (cannot be reset to anytype from interface)
- fmtstr
   new style python format: `{:}`

name, type, width, and fmtstr can all be edited on the Columns metasheet.

[will probably become getter(col, row) and setter(col, row, val).  Use col.sheet if needed]
[previously was %s C-style format, which I might still prefer]

### Column.sheet

Though I resisted this for a long time, Columns are now associated with their sheet; the same exact Column object cannot be used on multiple sheets.  In practice this seems okay; just use `Sheet.addColumn(copy(Column))` and addColumn will set the .sheet member of the new Column properly.

The Column's sheet is in the .sheet member, but that is not set until `Sheet.recalc()` (first reload).
This can be a problem when a getter or setter needs to know the sheet; it can't pass it into the constructor, and the getter is not given the column.  The solution is to assign columns in the reload() and bind the sheet in the lambda.


[same recursive lookup for colors as with commands]
[drop color precedence altogether; cell overrides row overrides col overrides hdr]
[attributes (bold, underline, reverse) always used for header/column/row and not configurable]

## Example

Here is an extremely simple sheet that shows a list of all global variables with their values:

    from vdtui import *


Notes:
- `Sheet.__init__(name, *sources, **kwargs)` sets the name and sources, as well as adding kwargs as extra attributes for convenience.
- source = sources[0]
   - having an internal concept of source/sources is maybe too complicated.  It does allow a dependency graph to be made, which might come in useful when we start doing code generation.
- columns are set in reload, because they require the sheet's context, for the source dict, to be bound to the lambda.  [Future: setter=lambda col,row,val: col.sheet.source[row] ]
- The structure of the row objects is so important that I have taken to including a 'rowdef' comment above every sheet, describing what kind of object each row is.
- The getters are passed into the Column init kwargs directly.  The default getter is the identity function, so the 'key' getter is actually unnecessary.
- There are other possible designs of this sheet:
   - rows could be list(self.source.items()); but then when an item changes, this sheet would not change until reload (^R)
   - could take generic dict; use source

## class VisiData and vd()

The VisiData singleton (accessible via `vd()` or `sheet.vd`) maintains:

- `scr`: the curses screen object
- `sheets`: a list; `sheets[0]` is the actively displayed sheet

`vd().windowWidth` and `vd().windowHeight` are the current window dimensions.

## run()

`VisiData.run(scr)` is the main display loop.  It calls `draw()` on the top sheet, left and right statuses, and handles commands, until there are no more sheets.  This times out every `curses_timeout`; everything is recomputed every frame if not cached.  This keeps the interface 'live'.

VisiData exits when this function returns.

This function must be called with the curses screen object.  Applications should instead call the module-level `run(*sheets)` with the sheets they want pushed initially, and VisiData will initialize curses to its liking.

[should the two run() functions have different names?]

## Sheet.draw(scr)

Handles drawing everything on the screen but the status bars.

`Sheet.calcColLayout()` uses:
   - `Sheet.leftVisibleColIndex`: leftmost visible non-key column

and computes:
   - `Sheet.visibleColLayout` (dict of vcolidx to (onscreen x, w)); only for onscreen columns
   - `Sheet.rightVisibleColIndex` (the rightmost visible column)
   - any None Column.width (sets to max width of values in onscreen rows)

For symmetry, there is also `Sheet.rowLayout` (dict of rowidx to onscreen y), computed during draw().
[allow variable height rows]

`Sheet.calcColLayout` should be called at least whenever a Column is added, deleted, or its width is changed.
In practice, it is called at the beginning of every draw cycle anyway.
It is also used to get a good 'feel' during pageLeft() and checkCursor().

### DisplayWrapper

For each cell, `Column.getCell(row)` produces a `DisplayWrapper`, which has the whole deal:
Cell returns DisplayWrapper, which is the whole deal; the original value, the fully typed and formatted display string, a note character and note color, associated error

- `value` the raw result returned from the getter
- `display` full string in the cell
- `error` if any error occurred (use getattr(error))
- `note` on far right of cell, in notecolor
- `notecolor`, text string ('green')

[DisplayWrapper will allow per-character colors; should colorizers be called before or after, or be subsumed by DW?]

getCell does the most amount of work per cell, and there are several other internal getters which do less work for a purpose other than display.  From the least amount of work to the most:

1. `Column.getValue(row)`
   The main function to call to get the raw value.  Will cache the result if `Column._cachedValues` is a mapping (which it is, if `cache=True` is in the Column init kwargs.
   (In VisiData proper, `z'` will add or reset the cache for the current column].
2. `Column.calcValue(row)`
   Computes the raw value every time.  This is the function to override if subclassing Column.
3. `Column.getTypedValue(row)`
   Produces a guaranteed result, coerced to Column.type.  When every cell in this column simply must have a value (like sort).
4. `Column.getCell(row)`
   This returns a DisplayWrapper no matter what.  It does type conversion, formatting, decoding, exception handling, and annotating.  The only thing it doesn't do is colorizing.
5. `Column.getDisplayValue(row)`
   Returns a guaranteed string value equivalent to what would be displayed in wide-enough cell.
   Deprecated: use `getCell(row).display` instead

In [execstr]s, `cursorValue` is equivalent to cursorCol.getValue(cursorRow)`, and so on with `cursorTypedValue`, `cursorCell`, and `cursorDisplay`.

