====================================
VisiData architecture for developers
====================================

VisiData is like a powerful spreadsheet from an alternate textpunk reality, in
which data can be easily manipulated from the keyboard and terminal.  Unlike a
spreadsheet, however, the data is well-structured, so that the data model is
closer to Pandas or an RDBMS.

* The main unit of functionality is the *sheet*. A ``vd`` instance contains a
  stack of sheets, the last of which (``vd.sheets[-1]``) is the one displayed.

* Sheets have *rows* and *columns*.

* Each sheet has a homogeneous list of rows, which can be any kind of Python
  object.

* Individual cells do not contain arbitrary values, but are extracted by the
  column from the particular Python object for that row. Unlike in a
  traditional spreadsheet, this is the primary function of a VisiData column.

Constraining the data to fit within this architecture simplifies the
implementation and allows for some radical optimizations to data workflow.


Columns
=======

Note that each ``Column`` object is detached from any sheets in which it
appears. Think of is as a lens through which each individual *row* of a sheet
is viewed. Every ``Column`` must have a name and a ``getter`` method.

Name and other properties
-------------------------

Columns have a few properties, all optional except for ``name``:
  
* **name**: should be a valid Python identifier and unique among
  the column names on the sheet. Some features may not work if these conditions
  are not met.
    
* **type**: defaults to ``str``; other values are ``int``, ``float``,
  ``date``. There is also a dummy ``anytype`` to produce a stringified version
  for anything not in these categories.
    
* **width**: specifies the default width for the column; ``0`` means
  hidden.
    
* **fmtstr**: format string for use with ``type`` when ``type`` is a date. 
    
* **aggregators**: a dictionary providing a few simple statistical
  functions (``sum``, ``mean``, ``max``, etc.).

* **expr**: Python expression that generates values if the column is a
  "computed column".


Getter and setter
-----------------

Each ``Column`` object has ``getter`` and ``setter`` methods; both are lambdas.
These lambdas are the "lenses" mentioned above — they are used on the fly to
display the cells of each row that (apparently) intersects with the column. 

Getter
~~~~~~

This lambda function is required. It takes a row as input and returns the value
for that column. This is the essential functionality of a ``Column``.

A ``getter`` has wrapper methods ``getValue`` and ``getDisPlayValue`` to
represent a value as its declared type or to format a value properly for
display.
    
Setter
~~~~~~

The ``setter`` lambda function allows a row to be modified by the user using
the ``Sheet.editCell`` method. It takes a row object and new value, and sets
the value for that column.

When a new ``Column`` object is initialized, ``setter`` defaults to ``None``,
making the column read-only (``Column.setValues``).

Normally when a
``Column`` object is instantiated in code rather than being read from a source,
the setter is defined as an argument to ``Column``. For example:

.. code-block:: python

   def ColumnAttr(attrname, type=anytype, **kwargs):
       'Return Column object with `attrname` from current row Python object.'
       return Column(attrname,
                     type=type,
                     getter=lambda r,b=attrname: getattr(r,b),
                     setter=lambda r,v,b=attrname: setattr(r,b,v),
                     **kwargs)

Built-in methods for column-creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ColumnAttr`` above is one of several built-in methods for constructing a
``Column`` object:

* ``ColumnAttr`` gets an attribute from the row object using
  ``visidata.getattr`` (and allows it to be set with ``visidata.setattr``).
  This is useful when the rows are Python objects. 
   
* Another is ``ColumnItem(colname, itemkey)``. It uses ``visidata.getitem``,
  which is useful when the rows are mapping objects.

* Two others are ``combineColumns``, ``SubrowColumn``, and
  ``visidata.ColumnItem``.

Because cell-values are computed on the fly by lambdas, they are hard to
observe in a REPL or using a conventional debugger. It may be useful to call
``Ctrl-o`` followed by ``sheet`` or ``vd.sheets``, to inspect sheets'
attributes visually.

Commands
========

Keyboard commands are the primary interface for the user to control VisiData.
Add new commands using the global ``command()`` function within a .py file.

Syntax
------

``command()`` takes three arguments:

* *command sequence*: the sequence of keys pressed to trigger the action. (Note
  that if the control-key is involved, control is represented by ``^`` and the
  following key must be upper-case. This is a stricture of Curses.)

* *exec string*: a string containing valid python code that will be passed to
  ``exec``. This string is limited to a single line of Python; longer code must
  be placed in a separate "`add-on <Extending VisiData>`_" module.

* *help string*: help text provided to users on the help sheet.

Example
-------

For example, VisiData has a builtin command ``Shift-P`` to take a random sample
of rows from the current sheet:

::

    command('P',
            'vd.push(sheet.copy("_sample")).rows=
                random.sample(rows, int(input("random population size: ")))',
            'push duplicate sheet with a random sample of <N> rows')

Here the command sequence is regular ASCII ``P``, but it could include one or
more prefixes or consist of a Curses `key constant
<https://docs.python.org/3/library/curses.html#constants>`_ (e.g.
``KEY_HOME``).

The ``exec`` string in this example illustrates the basic interface for
commands. Below we dissect

* The global ``VisiData`` singleton object is available as ``vd`` in the exec
  string (and ``vd()`` in other contexts).

* The ``VisiData.push`` method pushes a ``Sheet`` object onto the ``sheets``
  stack, making it the currently visible sheet. It returns that same sheet, so
  that a member (in this case, ``rows``) may be conveniently set without using
  a temporary variable.

* The current sheet is available as ``sheet``.

* The current sheet is also passed as the locals dict to ``exec``, so all Sheet
  members and methods can be read and called without referencing ``sheet``
  explicitly. **Note**: due to the implementation of ``Sheet.exec_command``,
  setting sheet members requires ``sheet`` to be passed explicitly. That is,
  when a sheet member variable is on the LHS of an assignment, it must be
  referred to as ``sheet.member`` or the assignment will not stick.

* The ``Sheet.copy`` member function takes a string, which is appended to the
  original sheet name to make the new sheet's name.

* ``random.sample`` is a builtin Python function. The ``random`` package is
  imported by VisiData (and thus available to all extensions automatically);
  other packages may be imported at the toplevel of the .py extension.

* ``input`` is a global function that displays a prompt and gets a string of
  input from the user (on the bottom line).

What can be done with commands
------------------------------

Anything is possible! However, the ``exec`` string limits functionality to
Python one-liners. More complicated commands require a custom sheet ("add-on")
to implement longer Python functions.

There will eventually be a VisiData API reference. In the meantime, please see
the source code for examples of how to accomplish most tasks.

Extending VisiData
==================

Extend VisiData by defining custom sheets, in an "add-on". An add-on is a
non-core Python module, available to VisiData if placed in ``visidata/addons``
and given a top-level key-binding that is available on all sheets. The add-on
returns specialized ``Sheet`` objects which are pushed onto the
``VisiData.sheets`` stack, initiated by a top-level command available on all
sheets.

Outline of syntax
-----------------

The skeleton of an add-on, apart from its actual functionality, is as follows:

* Subclass ``Sheet``. In ``__init__``:

  * Add a command (using ``command()``) that instantiates the class and pushes
    it onto a ``vd`` instance. You may also like to add options, using the
    ``option`` command

  * Call ``super`` to define the name of the new sheet.

  * The constructor passes the name of the sheet and any source sheets
    (available later as ``Sheet.source``).

  * Populate columns ``self.columns`` with a list of all possible columns.
    Each entry should be a ``Column`` object (or subclass) and should have a
    name.

  * Define any sheet-specific commands, using ``self.command()`` within the
    constructor. The arguments are identical to those of the global `command()
    <Commands>`_ function.
   
* Define ``reload`` to as to recompute the values of the rows. See
  `<``reload()``>`_ below.
   
* Consider whether the sheet may be so large or slow to recompute that you
  don't want to user to be blocked waiting for reloading to finish. Some
  sheets, such as the help sheet, cannot become that large and so there is
  no need for asynchronous handling. But if it may become large, then:
   
  * Use ``genProgress`` to display a progress bar showing the percentage of
    rows recomputed.
   
  * Decorate ``reload`` with `<``@async``>`_.
   
Example
~~~~~~~

Here is a simple sheet which makes a ``t`` command to "take" the current
cell from any sheet and append it to a predefined "journal" sheet. This
sheet can be viewed with ``Shift-T`` and then dumped to a ``.tsv`` file with
``^W`` (Ctrl-w).

::

    from visidata import *

    command('t',
            'vd.journal.rows.append([sheet, cursorCol, cursorRow])',
            'take this cell and append it to the journal')
    command('T', 'vd.push(vd.journal)', 'push the journal')

    option('fn_journal', 'journal.tsv', 'default journal output file')

    class JournalSheet(Sheet):
        def __init__(self):
            super().__init__('journal')

            self.columns = [
                Column('sheet', getter=lambda r: r[0].name),
                Column('column', getter=lambda r: r[1].name),
                Column('value', getter=lambda r: r[1].getValue(r[2])),
            ]

            self.command('^W',
                         'appendToJournalFile(); sheet.rows = []',
                         'append to existing journal and clear sheet')

        def appendToJournalFile(self):
            p = Path(options.fn_journal)
            writeHdr = not p.exists()

            with p.open_text('a') as fp:
                if writeHdr:
                    fp.write('\t'.join('sheet', 'column', 'value'))
                    status('created journal at %s' % str(p))
                for r in self.rows:
                    fp.write('\t'.join(col.getDisplayValue(r)
                                  for col in self.columns) + '\n')
                status('saved %d rows' % len(self.rows))

    vd().journal = JournalSheet()

Note that the ``t`` command includes ``cursorRow`` in the list instead
of ``cursorValue``, and the ``value`` column calls Column.getValue().
This is the desired pattern for appending rows based on existing sheets,
so that changes to the source row are automatically reflected in the
subsheets.

Custom VisiData applications
----------------------------

Import the ``visidata`` package into a Python script to create a custom VisiData application.

   
Other functionality
===================

Status bar
----------
   
The ``VisiData`` singleton has a list ``statuses`` that stores status-messages successively. Add a status message using ``VisiData.status``; there is also module-level wrapper ``status``, available to lambdas and ``eval``.
   
The on-screen status bar is composed in two parts, with ``VisiData.leftStatus`` and ``VisiData.rightStatus``; the two parts are drawn separately, with ``VisiData.drawLeftStatus`` and ``VisiData.drawRightStatus``.
  
Special to the ``Sheet`` object is method ``statusLine``, which returns the number of rows and the numbers of selected rows and columns.
   
Errors and debugging
--------------------
   
The ``VisiData`` singleton maintains a list ``lastErrors``, containing the most recent ten tracebacks. A traceback is added by ``VisiData.exceptionCaught``, which is normally called in the ``except`` clause of a ``try except`` block.
   
There is a module-level ``error`` function for use with lambdas and ``eval``.
   
The developer will find it useful to toggle debug-mode on with ``Ctrl-d``, to display error messages (without traceback) on the left side of the status bar.
   
Hooks
-----
   
Hooks for special functionality are stored in ``VisiData.hooks`` and supported with ``VisiData.addHook`` and ``VisiData.callHook``. At the moment, hooks are used mainly in ``editText``, the optional ``editlog`` addon, and before redrawing the screen.

Adding a new data source
------------------------

In the JournalSheet example above, the rows are added incrementally
during a user's workflow, so the ``reload()`` method is extremely simple.
(We may question whether it should even be there at all, but no matter.)

New data sources can also be integrated into VisiData, and the primary
difference is the ``reload()`` method. There are several existing
examples in the ``visidata/addons`` directory, and the general structure
looks like this:

Example
~~~~~~~

::

    from visidata import *

    class open_xlsx(Sheet):
        def __init__(self, path):
            super().__init__(path.name, path)
            self.workbook = None
            self.command(ENTER,
                         'vd.push(sheet.getSheet(cursorRow))',
                         'push this sheet')

        @async
        def reload(self):
            import openpyxl
            self.columns = [Column('name')]
            self.workbook = openpyxl.load_workbook(str(self.source),
                                                   data_only=True,
                                                   read_only=True)
            self.rows = list(self.workbook.sheetnames)

        def getSheet(self, sheetname):
            worksheet = self.workbook.get_sheet_by_name(sheetname)
            return xlsxSheet(join_sheetnames(self.source, sheetname),
                             worksheet)

    class xlsxSheet(Sheet):
        @async
        def reload(self):
            worksheet = self.source
            self.columns = ArrayColumns(worksheet.max_column)
            self.progressTotal = worksheet.max_row
            self.rows = []
            for row in worksheet.iter_rows():
                self.progressMade += 1
                self.rows.append([cell.value for cell in row])

New data sources are generally implemented with one or more subclasses
of Sheet.

To have a data source apply to files with extension ``.foo``, create a
class (or function) called ``open_foo``. This should return a new sheet
constructed from the given source, which will be a ``Path`` object
instead of a parent sheet.

This ``.xlsx`` example is fairly typical of real world data sources,
which often contain multiple datasets. In such a case, an index sheet is
pushed first, with an ``ENTER`` command to push one of the contained
sheets. The ``getSheet`` in this example is just a sheet-specific method
on the index sheet that constructs the chosen sheet.


Custom options
--------------

The ``option()`` global function allows a user-modifiable option to be
specified instead of using a hard-coded value.

*  The arguments are the option name, a default value, and a help string.

*  Options are available as attributes on the ``options`` object.

*  Options should always have a usable default.

*  Options should not be cached as the user can change them while the
   program is running.

``reload()``
------------

The ``reload()`` method (invoked with ``^R`` (Ctrl-R)) should in general
reset the sheet to its starting rowset, without changing the column
layout.

In the above example, ``reload()`` clears ``Sheet.rows`` before
reloading, to prevent the sheet from growing in size with every ``^R``.

``reload()`` is not called until the sheet is first viewed.

Note that ``import`` of non-standard Python packages should occur just
before their first use. In the case of data sources, that means in the
``reload()`` method itself. This is so that ``vd`` does not require external
packages to be installed unless they are actually needed for parsing a specific
data source.

``@async``
----------

Functions which can take a long time to execute may be decorated with
``@async``, which spawns a managed Task in a new thread to run the
function. This is especially useful for data sources which may require
loading large amounts of data.

Async functions should initialize ``Sheet.progressTotal`` to some
reasonable measure of total work, and they should also be structured to
frequently update ``Sheet.progressMade`` with the amount of work already
done. This is used for the progress meter on the right status line.

``editText``
------------

(Not yet documented.)

Regular expressions (regex)
---------------------------

(Not yet documented.)

Drawing
-------

(Not yet documented. Topics include ``colLayout`` and ``visibleCols``.)

Colorizing
----------

Control of the colors of foreground and background text is in need of work and
is not yet documented.

Theme colors and characters
---------------------------

(Not yet documented.)

Making VisiData apps
--------------------

(Not yet documented. Topics include ``set_global`` and the helper sheets
``TextSheet`` and ``DirSheet``.)

Making VisiData sources
-----------------------

(Not yet documented. Topics include ``Path`` objects, ``openSource``, and
``open_*``.)


