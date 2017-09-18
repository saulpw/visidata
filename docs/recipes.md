
These functions are included in vdtui, but the names made no sense and were harder to remember than the code.
These are the patterns that come up time and time again.
They are documented here as recipes; alter as needed and to taste.

# ColumnItem
ColumnItem uses `__getitem__` and `__setitem__` (like `row[key]`) with a bound `key` indexing the row.  Useful for sequences (tuple, list, str) and mappings (dict).

To make columns on a sheet where each row will be a 3-tuple:
```
    columns = [ColumnItem(name, i, type=int) for i, name in enumerate('xyz')]
```

or where each row is a dict (by default, the key is the name itself):

```
    self.rows = globals().values()
    self.columns = [ColumnItem(k, width=8) for k in self.rows[0]]
```

## ColumnAttr

ColumnAttr uses `getattr` and `setattr` (like `row.attr`) with a bound `attr` to get from the row.  Useful for rows of Python objects.

```
    self.rows = globals().values()
    self.columns = [ColumnAttr(attr) for attr in vars(self.rows[0])]
```

## SubrowColumn

SubrowColumn proxies for another Column, in which its row is nested in another sequence or /mapping.
Useful for augmented rows, like `tuple(orig_index, orig_row)`, for instance, for a sheet which copied a sheet, wrapping the original row in a tuple along with the original row number:

```
    self.rows = list(enumerate(orig_sheet.rows))
    self.columns = [ColumnItem('orig_index', 0)] + [SubrowColumn(c, 1) for c in orig_sheet.columns]
```
