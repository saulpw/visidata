

[viewtsv](https://github.com/saulpw/visidata/blob/stable/bin/viewtsv)
is a great example of a minimal vdtui application.

This is an extremely functional utility in 20 lines of code.

Annotated line by line:

1. Requires Python 3; v1.0 requires v3.4+.

4. Copy the vdtui.py into your application wholesale.  It's freely usable under the MIT license, and then you can just import it like this and use it without adding any external dependencies.

6. All tabular data sheets inherit from Sheet.

7. An initial column. normally the class-level `columns` is set to the actual columns of the sheet, but in this case, the columns aren't known until the source is loaded.
See reload():19. Not strictly necessary but makes loading a bit more responsive.

9. [@async](/design/async) marks the function to spawn a new thread whenever it is called.

10. The [`reload()`](/design/loaders) function collects data from the source and puts it into `rows`.  It's called once automatically when first pushed, and manually with `^R`.

11. `rows` is a list of Python objects.  The row definition ('rowdef') for the TsvSheet is a tuple of values, with each position corresponding to one column.

13. self.source is specified in the constructor as a [vdtui.Path](/api/Path).  `Path.open_text` returns a file-like object.

14. `rows` could be populated by a list comprehension, which might be more efficient overall, but reload() is structured this way as a deliberate append loop, so that the rows are available to the interface as the sheet is loading (as the sheet is async, see line 9).

15. Strip the included newline character.

16. Some .tsv have double double newlines (CRLFCRLF) and extra (blank) lines are returned.  This filters them out.

17. `addRow` just calls `rows.append()`. It seems like it might be a useful hook but nothing uses it yet.
Yes, much of this project is not strictly PEP8 compliant, as in the camelCase method names on Sheet.

19. The actual columns are set from the first (header) row.
ColumnItem is a builtin, which creates a column to use getitem/setitem with the given key/index.

20. The header row is removed from the list of rows.  (Column names are displayed on the first row anyway).

23. `run(*sheets)` is the toplevel entry point for vdtui.


---

