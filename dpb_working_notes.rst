## Working notes for VisiData

#. Variable-name conventions

   * ``c``: column

   * ``expr``: Python expression

   * ``D``, ``d``: dict

   * ``f``: function

   * ``fn``: filename

   * ``i``: target variable of iterator or generator

   * ``idx``: index

   * ``L``: list

   * ``p``: path
     
   * ``pv``: present value

   * ``r``: row

   * ``ret``: return value

   * ``rng``: range

   * ``s``: string

   * ``scr``: "screen" object in Curses

   * ``v``: name of variable

   * ``vd``: visidata, normally constructed as a singleton (one-time-only instance) as ``VisiData()``

   * ``vs``: sheet, constructed as ``visidata.Sheet(name, path)`` or returned from some function as ``openURL(path)``, ``open_tsv(path)``, ``DirSheet(name, path)``, etc.


#. Format of ``Row``

#. Format of ``Column``

#. Basic configuration of ``Sheet``

   * 'addColumn': function
   * 'calcColLayout': function
   * 'cellValue': function
   * 'checkCursor': function
   * 'clipdraw': function
   * 'command': function
   * 'copy': function
   * 'cursorCol': property
   * 'cursorColIndex': property
   * 'cursorDown': function
   * 'cursorRight': function
   * 'cursorRow': property
   * 'cursorValue': property
   * 'deleteSelected': function
   * 'draw': function
   * 'drawColHeader': function
   * 'editCell': function
   * 'exec_command': function
   * 'gatherBy': function
   * 'genProgress': function
   * 'isSelected': function
   * 'isVisibleIdxKey': function
   * 'keyColNames': property
   * 'keyCols': property
   * 'moveRegex': function
   * 'moveVisibleCol': function
   * 'nCols': property
   * 'nRows': property
   * 'nVisibleCols': property
   * 'nVisibleRows': property
   * 'name': property
   * 'nonKeyVisibleCols': property
   * 'pageLeft': function
   * 'progressPct': property
   * 'reload': function
   * 'rowColor': function
   * 'searchColumnNameRegex': function
   * 'searchRegex': function
   * 'select': function
   * 'selectByIdx': function
   * 'selectRow': function
   * 'selectedRows': property
   * 'skipDown': function
   * 'skipUp': function
   * 'source': property
   * 'statusLine': property
   * 'toggle': function
   * 'toggleKeyColumn': function
   * 'unselect': function
   * 'unselectByIdx': function
   * 'unselectRow': function
   * 'visibleColNames': property
   * 'visibleCols': property
   * 'visibleRows': property

#. Questions

   * With such parameters as ``VisiData.statusHistory`` (truncated to |100| on instantiation) and ``VisiData.exceptionCaught`` (truncated to |10|), rather than hard-coding these values, perhaps at some point they can be set via options.

#. Things to mention

   * Sheets are added to ``sheets`` at index 0, contrary to the usual practice of treating a list as a stack.

   * Commands are normally defined as lambdas.

   * Decorator ``@async`` (using ``threading``) is defined in ``vd.py``, for use with processes that potentially take a long time to finish. (Give examples.)

#. Revise ``%``-type string formatting to use ``str.format()``.

----

#. Tests.

   * We have an edit log, which can be used for testing. We play ("replay") the commands in a "test" log, and then compare the output with some "golden" output file.

   * Record the commands you want to test, open the Edit Log and replace the value of ``end_sheet`` with ``{input}`` for the first command (which should be ``o``). Replace the value of ``end_sheet`` with ``{output}`` for the last line containing ``^s``. Then compare qqq

   * Replay a ``.vd`` file using ``bin/vdplay``, a headless VD tool.

   * Only first four columns of ``.vd`` file matter for the test; the EditLog's "comment" column which contains the description of each keystroke by default, can be edited if you want other content there.

   * 

#. Attributes in color

   * bold, reverse, underline

   * 256 colors, can be viewed using ``bin/vdcolors``. Only a few have standard curses color names.

   * colors are listed as, e.g., ``215 yellow``, which means use color 215 if available, otherwise use ``yellow`` as fallback.

   * option ``num_colors``: if 0, take number of colors from Curses, otherwise use the number supplied.

   * Any option can be applied at the command line. See ``vs-help`` for listing. ``--`` and either ``=`` or space between the option and its value.

   * Attributes stack and colors don't.

   * Internally, we use ``Sheet.colorizers``. These static methods all return an option (which is a color string) and a precedence number; Higher numbers mean higher precedence. You add a function to the colorizers list and the program only takes the ones with the highest precedence.

   * On the options sheet, the colored rows are colored; this is done with ``OptionsSheet.colorOptionCell``, which is called by ``OptionsSheet.colorizers``. We validate the row and col, because the separators are represented by ``None`` (separators are not independently colorable).

   * Colors come as pairs: the ``reverse`` attribute is necessary to make colored backgrounds appear.

[end]
