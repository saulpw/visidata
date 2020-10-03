Interface
=========


Cursor
======

.. data:: visidata.TableSheet.cursorVisibleColIndex

Column cursor as an index into ``TableSheet.visibleCols``.  Settable.

.. data:: visidata.Sheet.cursorRowIndex

Row cursor as an index into ``TableSheet.rows``.  Settable.

.. data:: visidata.Sheet.topRowIndex

Top row on the screen, as an index into ``TableSheet.rows``.  Settable.

.. autoattribute:: visidata.Sheet.cursorCol
.. autoattribute:: visidata.Sheet.cursorColIndex
.. autoattribute:: visidata.Sheet.cursorValue
.. autoattribute:: visidata.Sheet.cursorTypedValue
.. autoattribute:: visidata.Sheet.cursorDisplay

.. autofunction:: visidata.Sheet.cursorDown
.. autofunction:: visidata.Sheet.cursorRight
.. autofunction:: visidata.Sheet.moveToNextRow
.. autofunction:: visidata.Sheet.moveToCol
.. autofunction:: visidata.Sheet.moveToRow

.. autofunction:: visidata.BaseSheet.checkCursor

Input/Edit
----------

.. autofunction:: visidata.vd.input
.. autofunction:: visidata.vd.confirm
.. autofunction:: visidata.vd.launchEditor

Status
------

.. autofunction:: visidata.vd.status
.. autofunction:: visidata.vd.warning
.. autofunction:: visidata.vd.fail

Colors
------

.. data:: visidata.TableSheet.colorizers

class member which specifies a list of Colorizers for this class.; similar to TableSheet.columns, to be 

Do not manually update this list to add colorizers on a specific sheet.
Instead use addColorizer and removeColorizer.

.. autofunction:: visidata.TableSheet.addColorizer
.. autofunction:: visidata.TableSheet.removeColorizer

Drawing
--------

.. autoattribute:: visidata.BaseSheet.windowWidth
.. autoattribute:: visidata.BaseSheet.windowHeight
.. autofunction:: visidata.BaseSheet.refresh
.. autofunction:: visidata.VisiData.redraw
.. autofunction:: visidata.BaseSheet.draw
.. autoclass:: visidata.SuspendCurses

::

    with SuspendCurses():
    @VisiData.api
    def launchPager(vd, *args):
        'Launch $PAGER with *args* as arguments.'
        args = [os.environ.get('PAGER') or vd.fail('$PAGER not set')] + list(args)
        with SuspendCurses():
            return subprocess.call(args)

::

    passwd = vd.input("password: ", display=False)

    # initial value is the formatted value under the cursor
    vd.status(vd.input("text to show: ", value=cursorDisplayValue))

Colorizers
^^^^^^^^^^

.. autoclass:: visidata.RowColorizer
.. autoclass:: visidata.ColumnColorizer
.. autoclass:: visidata.CellColorizer

The TableSheet allows whole cells to be colorized according to a Python function.


- *prec*: precedence
- *coloropt*: name of color option, or None
- *func*: a func(sheet, col, row, value) called for each cell.

``func(sheet, col, row, value)`` is a lambda function which should return a True value for the properties when coloropt should be applied. If coloropt is None, func() should return a coloropt (or None) instead.

Using colors in other curses contexts
-------------------------------------

If you want to get the attribute associated with a particular color/attribute combination.
ciolors
colors.color_

A color string contain a list of space-delimeated words that represent colors. Upon startup, VisiData's `ColorMaker` will try to compute these color strings by parsing each part as a [color](https://github.com/saulpw/visidata/blob/develop/visidata/color.py#L72) (red green yellow blue magenta cyan white, or a number if 256 colors available) or [attribute](https://github.com/saulpw/visidata/blob/develop/visidata/color.py#L76) (normal blink bold dim reverse standout underline). A 256-color palette is not guaranteed, however, and in that case a color like `238` would not exist.

With default colors, it is recommended that the second term be a basic color, to be used as a fallback. If the `238` is found, then it's used preferentially. (Attributes however are always applied).

Upon startup, a `ColorMaker` object is created. For each `theme()`, it translates the color strings into curses attributes. The setup `ColorMaker` is then importable in VisiData as `colors`. It contains a key for each color option name associated with its converted curses attribute (e.g. colors.color_graph_hidden or colors['color_graph_hidden']).


#### `RowColorizer`, `CellColorizer`, `ColumnColorizer`

A colorizer object is a simple named tuple, which VisiData employs to do property based coloring. Colorizers come in the form of `RowColorizer` (colors entire rows), `CellColorizer` (colors a single cell), and `ColumnColorizer` (colors an entire column).

Each of the named tuples contain the keys for 'precedence',  'coloropt', and 'func'.

Curses can combine multiple non-color attributes, but can only display a single color. Precedence is a number which indicates the priority a color has (e.g. if a row is selected, we want the selection color to trump the default color). A higher precedence color overrides a lower. `coloropt` is the color option name (like 'color_graph_hidden')


Set `colorizers` as a class member, and then add the `*Colorizers` to it in a list.

Examples
^^^^^^^^

::

    class DescribeSheet(ColumnsSheet):
        colorizers = [
            RowColorizer(7, 'color_key_col', lambda s,c,r,v: r and r in r.sheet.keyCols),
        ]

