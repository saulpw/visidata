=========================
The Screen for Developers
=========================

Screen layout and corresponding objects in code
===============================================

.. figure:: https://raw.githubusercontent.com/saulpw/visidata/stable/docs/img/visidata-interface.png
   :alt: screenshot
   
..

A. Column names in header row (bold). Value: ``Column.name``. Theme:
   ``color_default_hdr``.

B. Key columns (blue). Identified as ``keyCols == columns[:nKeys]``. Theme:
   ``color_key_col``.

C. '<'/'>' in header row indicate offscreen columns. There are more non-hidden
   columns offscreen if ``leftVisibleColIndex > nKeys or rightVisibleColIndex <
   nVisibleCols-1``. Theme: ``disp_more_left``/``disp_more_right`` Onscreen
   columns are represented as
   ``visibleCols[leftVisibleColIndex:rightVisibleColIndex+1]``.

D. Current column (bold with inverse header). Identified as ``cursorCol ==
   visibleCols[cursorVisibleColIndex]``. Theme ``color_current_col``.
   
E. Overflowing cells truncated with ellipsis character, ``…`` (``U+2026``).
   Theme: ``disp_truncator``.

F. Row cursor (inverse row). Value: ``Sheet.cursorRowIndex``. Theme:
   ``color_current_row``.

G. Selected rows (green). Value: ``Sheet._selectedRows``. Theme:
   ``color_selected_row``.
   
H. Sheet name and status line (lower left). Value: ``Sheet.name``. Theme:
   previous status, ``color_status``.

I. Current cell at intersection of current row and current column. Value:
   ``Sheet.cursorValue``.

J. Previously pressed keystrokes (lower right). Value: ``VisiData.keystrokes``.

K. Number of rows in sheet (lower right). Value: ``Sheet.nRows``.


----



The screen in Curses
====================

Below we describe issues involved in managing the screen using Curses. Most
properties and methods described here belong to ``Sheet``.

Terminal Window Size
--------------------

Available after the first time ``Sheet.draw()`` is called:

* ``windowWidth``

* ``windowHeight``

Rows
----

* ``cursorRow``
  
* ``cursorRowIndex``
  
* ``topRowIndex``

* ``rowLayout``

* ``visibleRows`` is a property, a list of row objects: the rows that are
  currently displayed in the terminal.

* ``nVisibleRows`` is simply based on ``windowHeight``. It assumes screen
  layout of one line for the headers, one line for the status, and one line per
  row.

* ``nRows``

Column layout
~~~~~~~~~~~~~

Column Visibility
.................

* `Key columns <#key-columns>`__ are always visible: they appear to be
   'pinned' to the left.

* Columns with ``width == 0`` are **hidden**.

Absolute and Visible Column Indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make column navigation feel intuitively smooth, the column cursor
should never alight on a 'hidden' column; for all purposes, hidden
columns should appear to be non-existent in the main sheet (even though
they will still be available on the columns metasheet). For example, a
column being moved with `H` or `L` should skip over any hidden columns.
[Whereas, on the columns metasheet, moving a "column" row up or down
will not skip over hidden columns.]

To make this convenient for column manipulation in general, there are
unfortunately two different column index spaces:

* *absolute indexes* that index into ``Sheet.columns``

* *visible indexes* that index into ``Sheet.visibleCols`` and
  ``Sheet.visibleColLayout``

When there are no hidden columns, these indexes are identical.

* ``cursorVisibleColIndex`` is a settable sheet variable that indicates
  where the column cursor is. ``cursorCol`` and ``cursorColIndex`` are
  properties derived from ``cursorVisibleColIndex`` in a very inefficient way,
  which may make large numbers (hundreds or more) of columns untenable.

* ``leftVisibleColIndex`` is a settable sheet variable that holds the
  visible column index of the left-most non-key column on the screen.

* ``rightVisibleColIndex`` is a cached sheet member that contains the
  rightmost recently calculated column on the screen.

* ``calcColLayout()`` recomputes the entire ``visibleColLayout`` dict, and
  sets ``rightVisibleColIndex`` based on the current layout. It also sets any
  onscreen ``Column.width`` that are None to the maximum width of the displayed
  rows.

Each ``visibleColLayout`` key (visible column index) maps to a simple
pair of ``(x, w)``, where ``x`` is the coordinate within the terminal, and
``w`` is the column width in characters.

``visibleColLayout`` always reflects the current layout displayed on the
screen. This may not be the layout for the next draw cycle, for example
if the currently executing command hides a column or causes the columns
to scroll.

* ``visibleCols`` and ``nonKeyVisibleCols`` are helpful properties, each
  returning a list of ``Column`` objects with the same ordering as
  ``Sheet.columns``, but omitting hidden columns.

* ``nVisibleCols`` is a property that returns the number of visible
  columns (i.e. one more than value of the maximum visible column
  index).

Key Columns
~~~~~~~~~~~

Key columns are '\_\_\_'.

* ``nKeys`` is a real member variable that determines the number of
  columns to use as keys.

* ``keyCols`` is a property that returns a list of the key columns.

Key columns are always the first ``nKeys`` columns in Sheet.columns.

Cells, Values, Types, and Formatting
------------------------------------

* ``cursorValue``

* ``setLeftVisibleColIndex()``, ``setRightVisibleColIndex()``

* ``cursorRight()``, ``cursorDown()``



