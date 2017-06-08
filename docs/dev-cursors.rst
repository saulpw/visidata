Screen layout
=============

terminal window size, available after first draw()
--------------------------------------------------

-  windowWidth
-  windowHeight

Rows
====

-  cursorRow
-  cursorRowIndex
-  topRowIndex
-  rowLayout {}

-  visibleRows (property; list of row objects): the rows that are
   currently displayed in the terminal
-  nVisibleRows: simply based on windowHeight, assumes screen layout of
   one line for the headers, one line for the status, and one line per
   row

-  nRows

Column layout
=============

Column Visibility
-----------------

-  `Key columns <#key-columns>`__ are always visible: they appear to be
   'pinned' to the left.
-  Columns with width == 0 are **hidden**.

Absolute and Visible Column Indexes
-----------------------------------

To make column navigation feel intuitively smooth, the column cursor
should never alight on a 'hidden' column; for all purposes, hidden
columns should appear to be non-existent in the main sheet (even though
they will still be available on the columns metasheet). For example, a
column being moved with 'H' or 'L' should skip over any hidden columns.
[Whereas, on the columns metasheet, moving a "column" row up or down
will not skip over hidden columns.]

To make this convenient for column manipulation in general, there are
unfortunately two different column index spaces:

-  *absolute indexes* which index into Sheet.columns
-  *visible indexes* which index into Sheet.visibleCols and
   Sheet.visibleColLayout

When there are no hidden columns, these indexes are identical.

*cursorVisibleColIndex* is a settable sheet variable that indicates
where the column cursor is. *cursorCol* and *cursorColIndex* are
properties derived from cursorVisibleColIndex in a very inefficient way,
which may make large numbers (hundreds or more) of columns untenable.

*leftVisibleColIndex* is a settable sheet variable that holds the
visible column index of the left-most non-key column on the screen.
*rightVisibleColIndex* is a cached sheet member that contains the
rightmost recently calculated column on the screen.

``calcColLayout()`` recomputes the entire visibleColLayout dict, and
sets *rightVisibleColIndex* based on the current layout. It also sets
any onscreen Column.width that are None to the maxwidth of the displayed
rows.

Each ``visibleColLayout`` key (visible column index) maps to a simple
pair of (x coordinate within the terminal, column width in characters).

``visibleColLayout`` always reflects the current layout displayed on the
screen. This may not be the layout for the next draw cycle, for example
if the currently executing command hides a column or causes the columns
to scroll.

-  *visibleCols* and *nonKeyVisibleCols* are helpful properties, each
   returning a list of Column objects with the same ordering as
   Sheet.columns, but omitting hidden columns.

-  *nVisibleCols* is a property that returns the number of visible
   columns (i.e. one more than value of the maximum visible column
   index).

Key Columns
-----------

Key columns are '\_\_\_'.

-  *nKeys* is a real member variable that determines the number of
   columns to use as keys.
-  *keyCols* is a property that returns a list of the key columns.

Key columns are always the first *nKeys* columns in Sheet.columns.

Cells, Values, Types, and Formatting
====================================

-  cursorValue

setLeftVisibleColIndex() setRightVisibleColIndex()

cursorRight() cursorDown()
