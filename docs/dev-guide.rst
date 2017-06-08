Overview of VisiData architecture
=================================

VisiData is like a powerful spreadsheet from an alternate textpunk
reality, in which data can be easily manipulated from the keyboard and
terminal. Unlike a spreadsheet, however, the data is well-structured, so
that the data model is closer to Pandas or an RDBMS.

-  The main unit of functionality is the *sheet*.
-  Sheets are divided into *rows* and *columns*.
-  Each sheet has a homogenous list of rows, which can be any kind of
   Python object.
-  Individual cells do not contain arbitrary values, but are extracted
   by the column from the particular Python object for that row.

In effect, a *column* is a lens through which each individual *row* is
viewed. Constraining the data to fit within this architecture simplifies
the implementation and allows for some radical optimizations to data
workflow.

Extending VisiData
==================

Extensions to VisiData can be added via Python code. These extensions
should be in files with a ``.py`` extension, which are passed on the
command-line. It is also possible to import the ``visidata`` package
from a Python script to create a `custom VisiData
application <vdapp>`__.

Add a new command
-----------------

Keyboard commands are the primary interface for the user to control
VisiData. Users can add new commands using the global ``command()``
function within a .py file.

``command()`` takes three arguments:

-  *command sequence*: the sequence of keys pressed to trigger the
   action

-  *exec string*: a string containing valid python code that will be
   passed to exec

-  *help string*: help text provided to users on the help sheet

For example, VisiData has a builtin command ``Shift-P`` to get a random
sample of rows from the current sheet:

::

    command('P',
       'vd.push(sheet.copy("_sample")).rows = random.sample(rows, int(input("random population size: ")))', 
       'push duplicate sheet with a random sample of <N> rows')

In this case the command sequence is just a regular ASCII ``P``, but the
command sequence could include one or more `prefixes <prefixes>`__
and/or be a curses keyname (e.g. ``KEY_HOME``).

This exec string illustrates the basic interface for commands:

-  The global VisiData singleton object is available as ``vd`` in the
   exec string (and ``vd()`` in other contexts).
-  The ``VisiData.push`` method takes a Sheet object and pushes it onto
   the sheet stack, making it the currently visible sheet. It returns
   the same Sheet, so that a member (in this case, ``rows``) may be
   conveniently set without using a temporary variable.
-  The current sheet is available as ``sheet``.
-  The current sheet is also passed as the locals dict to exec, so all
   Sheet members and methods can be read and called without referencing
   ``sheet`` explicitly. **Note: due to the implementation of
   ``Sheet.exec_command``, setting sheet members requires ``sheet`` to
   be passed explicitly. That is, when a sheet member variable is on the
   LHS of an assignment, it must be referred to as ``sheet.member`` or
   the assignment will not stick.**
-  The ``Sheet.copy`` member function takes a string, which is appended
   to the original sheet name to make the new sheet's name.
-  ``random.sample`` is a builtin Python function. The ``random``
   package is imported by VisiData (and thus available to all extensions
   automatically); other packages may be imported at the toplevel of the
   .py extension.
-  ```input`` <>`__ is a global function that displays a prompt and gets
   a string of input from the user (on the bottom line).

What can be done with commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anything is possible! However, the exec string limits functionality to
Python one-liners. More complicated commands will require a custom sheet
to implement longer Python functions.

There will eventually be a VisiData API reference. In the meantime,
please see the source code for examples of how to accomplish most tasks.

Creating a new sheet
--------------------

Developers can specify more advanced user interfaces are implemented
using custom sheets. These sheets are created and pushed with a toplevel
command available on all sheets, with a more highly-tuned workflow
becoming available when the custom sheet is visible.

Example
~~~~~~~

Here is a simple sheet which makes a ``t`` command to 'take' the current
cell from any sheet and append it to a predefined "journal" sheet. This
sheet can be viewed with ``Shift-T`` and then dumped to a .tsv file with
``Ctrl-W``.

::

    from visidata import *

    command('t', 'vd.journal.rows.append([sheet, cursorCol, cursorRow])', 'take this cell and append it to the journal')
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
                    fp.write('\t'.join(col.getDisplayValue(r) for col in self.columns) + '\n')
                status('saved %d rows' % len(self.rows))

    vd().journal = JournalSheet()

Note that the ``t`` command includes ``cursorRow`` in the list instead
of ``cursorValue``, and the ``value`` column calls Column.getValue().
This is the desired pattern for appending rows based on existing sheets,
so that changes to the source row are automatically reflected in the
subsheets.

Sheet initialization
--------------------

-  All custom sheets must inherit from ``Sheet``.
-  The constructor passes the name of the sheet and any source sheets
   (which are available later as ``Sheet.source``).
-  The constructor should also set up the columns and the sheet-specific
   commands.

Custom options
--------------

The ``option()`` global function allows a user-modifiable option to be
specified instead of using a hard-coded value.

-  The arguments are the option name, a default value, and a help
   string.
-  Options are available as attributes on the ``options`` object.
-  Options should always have a usable default.
-  Options should not be cached as the user can change them while the
   program is running.

Defining a sheet-specific command
---------------------------------

Use ``self.command()`` within the constructor. The arguments are
identical to the global ``command()`` function.

Column definition
-----------------

Set ``self.columns`` to a list of all possible columns. Each entry
should be a ``Column`` object (or subclass).

Using the base Column class
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The first argument is the column name, which should be a valid Python
   identifier (i.e. only letters, numbers and underscores). It should
   also be unique among column names on the sheet. These are not hard
   requirements (any name is acceptable, including no name), but several
   features will not work unless they are valid identifiers.
-  The only other essential argument is a getter function, which takes a
   row and returns the value for that column.
-  Optional named arguments:
-  ``type`` can be passed explicitly. Valid values are ``int``,
   ``float``, ``date``, ``str``. Columns that are not explicitly typed
   will be stringified just before being displayed.
-  a ``setter`` function allows a row to be modified by the user using
   the ``Sheet.editCell`` method. The setter takes a row object and new
   value, and sets the value for that column. Without a setter, the
   column can't be modified.
-  ``width`` specifies the default width for the column; ``0`` means
   hidden.

Helpful column creators
~~~~~~~~~~~~~~~~~~~~~~~

VisiData provides some utility classes to make it easier to create
common types of columns. The most common are:

-  ``ColumnAttr(attrname)`` gets an attribute from the row object using
   ``getattr`` (and allows it to be set with ``setattr``). Useful when
   the rows are Python objects.
-  ``ColumnItem(colname, itemkey)`` uses ``getitem``, which is useful
   when the rows are mapping objects.

Adding a new data source
========================

In the JournalSheet example above, the rows are added incrementally
during a user's workflow, so the ``reload()`` method is extremely simple
(if it should even be there at all).

New data sources can also be integrated into VisiData, and the primary
difference is the ``reload()`` method. There are several existing
examples in the ``visidata/addons`` directory, and the general structure
looks like this:

Example
-------

::

    from visidata import *

    class open_xlsx(Sheet):
        def __init__(self, path):
            super().__init__(path.name, path)
            self.workbook = None
            self.command(ENTER, 'vd.push(sheet.getSheet(cursorRow))', 'push this sheet')

        @async
        def reload(self):
            import openpyxl
            self.columns = [Column('name')]
            self.workbook = openpyxl.load_workbook(str(self.source), data_only=True, read_only=True)
            self.rows = list(self.workbook.sheetnames)

        def getSheet(self, sheetname):
            worksheet = self.workbook.get_sheet_by_name(sheetname)
            return xlsxSheet(join_sheetnames(self.source, sheetname), worksheet)

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

``reload()``
~~~~~~~~~~~~

The ``reload()`` method (invoked with ``^R`` (Ctrl-R)) should in general
reset the sheet to its starting rowset, without changing the column
layout.

In the above example, ``reload()`` clears ``Sheet.rows`` before
reloading, to prevent the sheet from growing in size with every ``^R``.

``reload()`` is not called until the sheet is first viewed.

Note that ``import`` of non-standard Python packages should be just
before their first use; in the case of data sources, in the ``reload()``
method itself. This is so that ``vd`` does not require external packages
to be installed unless they are actually needed for parsing a specific
data source.

``@async``
~~~~~~~~~~

Functions which can take a long time to execute may be decorated with
``@async``, which spawns a managed Task in a new thread to run the
function. This is especially useful for data sources which may require
loading large amounts of data.

Async functions should initialize ``Sheet.progressTotal`` to some
reasonable measure of total work, and they should also be structured to
frequently update ``Sheet.progressMade`` with the amount of work already
done. This is used for the progress meter on the right status line.

--------------
