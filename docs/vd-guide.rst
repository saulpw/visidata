==========================================
User Documentation for VisiData Components
==========================================


Additional Cursor Movements
---------------------------

-  ``z`` prefix scrolling (most behave exactly like vim).

    -  ``zt`` scrolls the current row to the top of the screen.

    -  ``zz`` scrolls the current row to the center of the screen.

    -  ``zb`` scrolls the current row to the bottom of the screen.

    -  ``zk`` scrolls one row up.

    -  ``zj`` scrolls one row down.

    -  ``zH`` moves the cursor one page to the left.

    -  ``zL`` moves the cursor one page to the right.

    -  ``zh`` moves the cursor one column to the left.

    -  ``zl`` scrolls the sheet one column to the right.

    -  ``zs`` scrolls the sheet to the leftmost column.

    -  ``ze`` scrolls the sheet to the rightmost column.

- ``c`` move to a column whose name matches a regex search.

- ``r`` move to a specified row number.


Manipulating Sheet Contents
===========================

Columns
-------

-  ``^`` edits a column's name

-  ``!`` makes the current column a *key column*.

- ``H``/``L`` moves the current column (left/right).

-  Columns generally start out ``anytype``.
    -  A column can be manually set to a specific type:

       -  ``~`` : ``str``

       -  ``#`` : ``int``

       -  ``%`` : ``float``

       -  ``$`` : ``currency`` (a float that strips leading and/or trailing non-numeric characters)

       -  ``@`` : ``date`` (datetime wrapper)

    -  All values are stored in their original format, and only converted on demand and as needed.

    -  Values that can't be properly converted are flagged with ``?`` at the right edge of the cell.

       -  For commands like sort (``[``/``]``) which require a correctly typed value, the default (0) value for that type is used.

    -  Cell edits are rejected if they don't convert to the column type.

-  ``:`` splits the current column into multiple columns based on a provided separator

    -  The cursor must be on an "example" row, to know how many columns to create.

- ``;`` creates new columns from the capture groups of the given regex (also needs example row)

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

Rows
----

- ``a``\ppends a blank row

- ``J``/``K`` moves the current row up/down.

Toolkit
=======

Statistics
----------

-  ``+`` on the source sheet allows selection of a statistical aggregator for this column

    - Existing aggregators can be viewed and set in the ``C``\olumns sheet

    - see `tour 01 <http://github.com/saulpw/visidata/tree/stable/docs/tours.rst>`_ for an example usage

-  ``Shift-F``\ requency table for current column with histogram

    - with a numeric column, ``w`` toggles between bins with an even interval width and bins with an even frequency height

Joining two datasets
--------------------

-  ``+`` joins selected columns on ``C``\olumns sheet

-  When sheets are joined, the rows are matched by the display values in the key columns. Different numbers of key columns cannot match (no partial keys and rollup yet). The join types are:

   -  ``&``: Join all selected sheets, keeping only rows which match keys on all sheets (inner join)

   -  ``+``: Join all selected sheets, keeping all rows from first sheet (outer join, with the first selected sheet being the "left")

   -  ``*``: Join all selected sheets, keeping all rows from all sheets (full join)

   -  ``~``: Join all selected sheets, keeping only rows NOT in all sheets (diff join)

Python objects
--------------

-  ``Ctrl-x`` to eval an expression and browse the result as a python object

