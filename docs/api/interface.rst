Drawing
========

These functions should rarely be necessary to use.
``BaseSheet.draw`` must be overridden on non-tabular sheets.

.. autofunction:: visidata.BaseSheet.refresh
.. autofunction:: visidata.vd.redraw
.. autofunction:: visidata.BaseSheet.draw

.. autoclass:: visidata.SuspendCurses

Window
========

.. autoattribute:: visidata.BaseSheet.windowWidth
.. autoattribute:: visidata.BaseSheet.windowHeight

.. data:: visidata.TableSheet.topRowIndex

Top row in the window, as an index into ``TableSheet.rows``.  Settable.

.. data:: visidata.TableSheet.leftVisibleColIndex

Leftmost column in the window (after key columns), as an index into ``TableSheet.visibleCols``.  Settable.

Cursor
======

Every Sheet has a cursor, which makes it easy to interact individual elements and slices of data.

A ``TableSheet`` has a row cursor and a column cursor, which overlap on a single cell.

.. data:: visidata.TableSheet.cursorVisibleColIndex

Column cursor, as an index into ``TableSheet.visibleCols``.  Settable.

.. data:: visidata.TableSheet.cursorRowIndex

Row cursor as an index into ``TableSheet.rows``.  Settable.

.. autofunction:: visidata.BaseSheet.checkCursor

.. autoattribute:: visidata.TableSheet.cursorCol
.. autoattribute:: visidata.TableSheet.cursorValue
.. autoattribute:: visidata.TableSheet.cursorTypedValue
.. autoattribute:: visidata.TableSheet.cursorDisplay

.. autofunction:: visidata.TableSheet.cursorDown
.. autofunction:: visidata.TableSheet.cursorRight
.. autofunction:: visidata.TableSheet.moveToNextRow
.. autofunction:: visidata.TableSheet.moveToCol
.. autofunction:: visidata.TableSheet.moveToRow

.. _input:

Input
======

.. autofunction:: visidata.vd.input
.. autofunction:: visidata.vd.choose
.. autofunction:: visidata.vd.chooseOne
.. autofunction:: visidata.vd.chooseMany
.. autofunction:: visidata.vd.confirm
.. autofunction:: visidata.vd.launchEditor

.. _status:

Status
======

.. autofunction:: visidata.vd.status
.. autofunction:: visidata.vd.warning
.. autofunction:: visidata.vd.fail
.. autofunction:: visidata.vd.exceptionCaught
.. autoclass:: visidata.ExpectedException

Examples
^^^^^^^^

::

    with SuspendCurses():
        try:
            return subprocess.call('less', '/etc/passwd')
        except Exception as e:
            vd.exceptionCaught(e)

::

    passwd = vd.input("password: ", display=False)

    # initial value is the formatted value under the cursor
    vd.status(vd.input("text to show: ", value=cursorDisplay))

.. _colors:

Colors
======

The TableSheet allows rows, columns, or individual cells to be colorized according to a Python function.

See `Color Docs <docs/colors>`__ for information on how to configure specific colors and attributes.

.. data:: visidata.TableSheet.colorizers

List of Colorizers for this class.  Class member.

Do not manually update this list to add colorizers on a specific sheet.
Instead use addColorizer and removeColorizer.

.. autofunction:: visidata.TableSheet.addColorizer
.. autofunction:: visidata.TableSheet.removeColorizer

.. autoclass:: visidata.DisplayWrapper

.. autoclass:: visidata.RowColorizer
.. autoclass:: visidata.ColumnColorizer
.. autoclass:: visidata.CellColorizer

- *precedence*: use color from colorizer with the greatest *precedence* value.
- *coloropt*: name of color option, or ``None``.
- *func*: ``func(sheet, col, row, value)`` is called for each cell as it is being rendered. Return True when *coloropt* should be applied to the cell.  If *coloropt* is None, ``func(...)`` can return the relevant coloropt (or None) instead.

- Attributes (underline, bold, reverse) combine, regardless of *precedence*.  Only colors will override other.

- The *value* passed to the Colorizer *func* is a ``DisplayWrapper``, which encapsulates the entirety of a displayed cell.  Use ``val.value`` to get the typed value (or None), or ``val.display`` for the displayed string.

.. note::

    Colorizers are called for headers and separators, in addition to cells.
    For a header, *row* will be None; for a separator, *col* will be None.
    So a RowColorizer needs to include a check that *row* is valid, a ColumnColorizer needs to check that *col* is valid, and a cell colorizer needs to check both.
    A simple check for non-False (see Examples) is sufficient.



Examples
^^^^^^^^

::

    class DescribeSheet(ColumnsSheet):
        colorizers = [
            # colors key 'rows' on the like key columns
            RowColorizer(7, 'color_key_col', lambda s,c,r,v: r and r in r.sheet.keyCols),
        ]

    class OptionsSheet(TableSheet):
        colorizers = [
            # colors cells
            CellColorizer(3, None, lambda s,c,r,v: v.value if r and c in s.columns[1:3] and r.name.startswith('color_') else None)
        ]
