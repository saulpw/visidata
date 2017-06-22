==========
User Guide
==========

Basic Movement and Essential Commands
=====================================

-  ``hjkl`` or arrow keys move the cursor around (left/down/up/right)
-  ``F1`` opens command help for the current sheet
-  ``q`` quits the current sheet (backs out one level); in a pinch,
   ``Ctrl-Q`` will force-quit the program entirely

Advanced movement
=================

Scrolling
---------

"Scrolling" adjusts the onscreen visible slice, but will not change the
current cursor position.

-  ``z`` prefix scrolling (most behave exactly like vim):

   -  ``zt`` scrolls current row to top of screen
   -  ``zz`` scrolls current row to middle of screen
   -  ``zb`` scrolls current row to bottom of screen
   -  ``zH`` moves cursor one page to left
   -  ``zL`` moves cursor one page to right
   -  ``zh`` moves cursor one column to left
   -  ``zl`` scrolls sheet one column to right
   -  ``zs`` scrolls sheet to leftmost column
   -  ``ze`` scrolls sheet to rightmost column
   -  ``zk`` scrolls one row up
   -  ``zj`` scrolls one row down

-  ``Home`` and ``End`` move the cursor to the first and last row of the
   entire sheet, respectively. The column cursor position is maintained.
-  ``PageUp`` and ``PageDown`` move the cursor exactly one onscreen page
   up or down. ``Ctrl-B`` and ``Ctrl-F`` do the same

-  The ``g`` prefix modifies movement commands by making them go "all
   the way".

   -  ``gk`` and ``gj`` are the same as ``Home`` and ``End``,
      respectively.
   -  ``gh`` and ``gl`` move the cursor to the first and last column.

Arranging Columns
=================

-  ``-`` (minus) hides a column
-  ``_`` (underscore) adjusts a column's width so that the entire
   contents of its cells are visible.
-  ``^`` sets a column's name
-  ``!`` makes the current column a *key column*.

Column Types
------------

-  columns start out untyped (unless the source data is typed)
-  ``~`` sets column type to str
-  ``#`` sets column type to int
-  ``$`` sets column type to currency
-  ``%`` sets column type to float
-  ``@`` sets column type to date

-  all values are stored in their original format, and only converted on
   demand and as needed.
-  values that can't be properly converted are flagged with ``~`` on the
   display
-  for commands like sort which require a correctly typed value, the
   default (0) value for that type is used
-  cell edits are rejected if they don't convert to the column type

Creating new columns
--------------------

-  ``:`` split column (on any sheet)
-  ``=`` "add column expression" takes a Python expression as input,
   evaluates the expression, and appends the results into a new column.
   Column names can be supplied as variables, in order to have the
   expression performed on the column cell-by-cell.

   -  Example: Suppose there is a column named ``Foo`` and a column
      named ``Bar``. ``=Foo+Bar`` would result in a column named
      ``Foo+Bar`` whose first row is the sum of the first row of ``Foo``
      and the first row of ``Bar``. Its second row would be the sum of
      the second row of ``Foo`` and the second row of ``Bar``, and so
      on.

-  ``+`` join selected columns on Columns sheet

Searching/Selecting/Deleting rows
=================================

-  ``[``/``]`` sort asc/desc by one column

Modifying data
==============

-  ``Ctrl-S``\ ave to ``.csv`` or ``.tsv`` (by extension)
-  ``e``\ dit cell contents

   -  Edits made to a joined sheet are by design automatically reflected
      back to the source sheets.

Special Sheets
==============

-  ``F``\ requency table for current column with histogram
-  ``Ctrl-O`` to eval an expression and browse the result as a python
   object

Metasheets
----------

-  ``S``\ heets metasheet to manage/navigate multiple sheets
-  ``C``\ olumns metasheet

   -  On the ``C``\ olumns sheet, these commands apply to rows (the
      columns of the source sheet), instead of the columns on the
      Columns sheet

      -  ``-`` hides column (sets width to 0)
      -  ``_`` maximizes column width to fit longest value
      -  ``!`` marks column as a key column (pins to the left and
         matches on sheet joins)

-  ``O``\ ptions sheet to change the style or behavior
-  ``^E``\ rror metasheet
-  ``^T``\ hreads metasheet

Glossary
========

Definitions of terms used in the help and documentation:

-  'go': move cursor
-  'move': change layout of visible data
-  'show': put on status line
-  'scroll': change set of visible rows

-  'push': move a sheet to the top of the sheets list (thus making it
   immediately visible)
-  'open': create a new sheet from a file or url
-  'load': reload an existing sheet from in-memory contents

-  'jump': change to existing sheet
-  'drop': drop top (current) sheet
-  'this': current [row/column/cell] ('current' is also used)
-  'abort': exit program immediately

Here are slightly better descriptions of some non-obvious commands:

-  the "``g``\ lobal prefix": always applies to the next command only,
   but could mean "apply to all columns" (as with the regex search
   commands) or "apply to selected rows" (as with ``d``\ elete) or
   "apply to all sheets" (as with ``q``). The global\_action column on
   the Help Sheet shows the specific way the global prefix changes each
   command.

-  ``R`` sets the source type of the current sheet. The current sheet
   remains until a reload (``Ctrl-R``).

-  When sheets are joined, the rows are matched by the display values in
   the key columns. Different numbers of key columns cannot match (no
   partial keys and rollup yet). The join types are:

   -  ``&``: Join all selected sheets, keeping only rows which match
      keys on all sheets (inner join)
   -  ``+``: Join all selected sheets, keeping all rows from first sheet
      (outer join, with the first selected sheet being the "left")
   -  ``*``: Join all selected sheets, keeping all rows from all sheets
      (full join)
   -  ``~``: Join all selected sheets, keeping only rows NOT in all
      sheets (diff join)

