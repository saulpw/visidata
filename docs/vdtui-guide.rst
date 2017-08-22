============================
User Documentation for vdtui
============================


Essential Commands
==================

Keystrokes for the cautious
---------------------------

-  ``F1`` or ``z?`` open command help for the current sheet.

-  ``q`` quits the current sheet (backs out one level) ; ``gq`` drops all of the sheets (clean exit).

-  ``Ctrl-q`` aborts the program immediately.

- ``Ctrl-c`` aborts a command which is expecting an input.

Moving the cursor
-----------------

-  ``hjkl`` or an arrow key move the cursor to an adjacent cell (left/down/up/right).

-  ``<Home>`` or ``<End>`` move the cursor to the first and last row of the entire sheet.

-  ``<PageUp>`` or ``<PageDown>`` move the cursor exactly one onscreen page up or down. ``Ctrl-b`` (backward) or ``Ctrl-f`` (forward) do the same.

-  The ``g`` prefix modifies movement commands by making them go "all the way".

   -  ``gk`` and ``gj`` are the same as ``Home`` and ``End``, respectively.

   -  ``gh`` and ``gl`` move the cursor to the first and last column.

- ``<``/``>`` move the cursor up/down this column to the next cell with a unique value.

- ``{``/``}`` move the cursor up/down this column to the next selected row.

- ``/``/``?`` search this column forward/backward with regex search; ``g/``/``g?`` search all columns.

  - ``n``/``N`` move the cursor to the next/previous match.


Manipulating Sheet Contents
===========================

Columns
-------

-  ``-`` (minus) hides a column.

    - To unhide a column, go to the ``C``\olumns sheet and ``e``\dit the width.

-  ``_`` (underscore) toggles a column's width between 'enough' (such that the entire contents of the onscreen cells are visible), and 'reasonable' (set by ``options.default_width``); ``g_`` sets all visible columns to 'enough'.

Rows
----

- ``s`` selects a row; ``gs`` selects all rows.

- ``u`` unselects a row; ``gu`` unselects all rows.

- ``<SPACE>`` toggles the selection of a row; ``g<SPACE>`` toggles the selection of all rows.

- ``|`` selects rows matching by regex in this column; ``g|`` in any visible column.

- ``\`` unselects rows matching by regex in this column; ``g\`` in any visible column.

- ``,`` selects rows matching this row in this column; ``g,`` in all visible columns.

- ``"`` pushes a duplicate sheet with only the selected rows; ``g"`` with all rows.

-  ``[``/``]`` sort ascending/descending by this column; ``g[``/``g]`` by all *key columns*.

Cells
-----

-  ``e``\ dit cell contents.

- ``ge`` edits the cell contents of all of the selected rows.

- ``Shift-V``\iew contents of this cell in a new sheet.


Metasheets 
==========

- ``Shift-S`` opens the Sheet metasheet.

    - allows management and navigation of the sheet stack. 

- ``Shift-C`` opens the Columns metasheet.

    - each row refers to a column on the source sheet.

    -  permits adjustments to various column parameters (such ``column_width``).

    - column modifying keystrokes (e.g., ``-``, ``_``, ...) will apply to the rows in the ``C``\olumns metasheet, and will result in modifications to the respective column in the source sheet.

- ``Shift-O`` opens the Options metasheet.

    - this will allow changes be made to style or behavior.

    - *Note*:currently the only way to set an option to ``False`` is to pass an empty string.

- ``<backtick>`` pushes the source of the current sheet.


Additional Tools
================

Developer aids
--------------

- ``Ctrl-e`` displays the stack trace for the most recent error; ``gCtrl-e`` for more errors.

- ``Ctrl-d`` toggles debug mode (any exception aborts the program immediately).

A few other keys
----------------

- ``Ctrl-l`` refreshes the terminal screen.

- ``Ctrl-r`` reloads the sheet from the source.

- ``Ctrl-g`` shows row/column details for the current sheet.

- ``Ctrl-v`` displays current version of the app.

.visidatarc
-----------
Allows you to customize VisiData settings across every session.

A sample ``.visidatarc`` is

::

    options.color_key_col = "cyan"

This configures key columns to be colored 'cyan'.


Glossary
========

Definitions of terms used in the help and documentation:

-  'abort': exit program immediately
-  'drop': drop top (current) sheet
-  'go': move cursor
-  'jump': change to existing sheet
-  'load': reload an existing sheet from in-memory contents
-  'move': change layout of visible data
-  'open': create a new sheet from a file or url
-  'push': move a sheet to the top of the sheets list (thus making it
   immediately visible)
-  'scroll': change set of visible rows
-  'show': put on status line
-  'this': current [row/column/cell] ('current' is also used)

Here are slightly better descriptions of some non-obvious commands:

-  the "``g``\ lobal prefix": always applies to the next command only,
   but could mean "apply to all columns" (as with the regex search
   commands) or "apply to selected rows" (as with ``d``\ elete) or
   "apply to all sheets" (as with ``q``). The global\_action column on
   the Help Sheet shows the specific way the global prefix changes each
   command.

