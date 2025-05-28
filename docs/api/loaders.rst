Loaders
=======

.. note::

    You are welcome to submit new loaders to core VisiData, or as plugins. Please, see our `checklists for contribution <https://visidata.org/docs/contributing>`__.

Creating a new loader for a data source is simple and straightforward.

1. ``open_filetype`` boilerplate
2. ``FooSheet`` subclass with rowtype and rowdef
3. ``FooSheet`` reload or iterload
4. ``FooSheet.columns``

Hello Loader
------------

Here's a step-by-line breakdown of a basic loader, which reads in a text file as a series of lines.
This same general structure and process should work for all loaders.

Step 1. ``open_<filetype>`` boilerplate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    @VisiData.api
    def open_readme(vd, p):
        return ReadmeSheet(p.base_stem, source=p)

This is used for filetype ``readme``, which is used for files with extension ``.readme``, or when specified manually with the ``filetype`` option like ``--filetype=readme`` or ``-f readme`` on the command line.

The ``open_<filetype>`` function usually looks exactly like this, with only the type of :ref:`Sheet <sheets>` changed.

The *p* argument is a :ref:`visidata.Path<vd-path>`.

The actual loading happens in the Sheet.  An existing :ref:`sheet type<sheets>` can be used, or a new sheet type can be created.

::

Step 2. Create a Sheet subclass
-------------------------------

::

    class ReadmeSheet(TableSheet):
        rowtype = 'lines'   # rowdef: [str]

-  TableSheet (and its alias ``Sheet``) is the basic tabular sheet of rows
   and columns. Most loader sheets will inherit from TableSheet, but
   some might inherit from more specialized sheets if they share
   functionality, or from ``BaseSheet`` if they are not tabular (like
   the ``Canvas``).

-  The ``rowtype`` member is only displayed on the :ref:`right-hand
   status <status>`. It should be **plural**. If not given, it is
   "``rows``". It's helpful to give the user an subconscious check of
   the kind of sheet being shown.

-  The ``rowdef`` should be given for all loaders, even though it is
   only a comment. It specifies the expected Pythonic structure of the
   rows on this sheet. This is important because nearly every other
   component of the sheet depends on this structure.

Step 3. Load data into rows, and yield them one-by-one
------------------------------------------------------

``reload()`` is called when the Sheet is first pushed, and thereafter by the user with :kbd:`Ctrl+R`.
The default ``TableSheet.reload()`` iterates through the rows returned by ``TableSheet.iterload()``, and takes care of a few common tasks (like running async and resetting the ``rows`` member to a new list).

Each loader for a tabular sheet should overload ``iterload()``, which uses the Sheet ``source`` to populate and then yield each row one-by-one.

::

    class ReadmeSheet(TableSheet):
        rowtype = 'lines'   # rowdef: [str]

        def iterload(self):
            for line in self.source:
                yield [line]

.. warning::
   ``str`` by itself is not a valid rowdef.

   Each row must have a unique *rowid*, which by default is the Python ``id()`` of the row.
   Because Python interns common strings, strings with the same value will have the same *id*.
   This would break a lot of features, like row selection for instance.

   Also, as an immutable type, it would be annoying to not be able to modify it.

   So it needs to be wrapped in a Python ``list``, which is guaranteed to be unique, and also mutable.


-  ``sheet.source`` is the :ref:`visidata.Path<vd-path>` given as the *source* kwarg to ``ReadmeSheet()`` in ``open_readme``. 

  .. note::

     Any *kwarg* passed to a Sheet constructor will be stored on the sheet in an attribute of the same name.

  .. note::

    `visidata.Path <vd-path>` objects are Path-like but have some additional features, like being iterable (yielding their contents one line at a time).

   While there is a ``visidata.Path.read_text()`` function, do **not** use ``for line in p.read_text().splitlines()`` in a loader, as that will read the entire file before returning the first line.
   A loader must be able to handle arbitrary amounts of data (including data too large to fit in memory), so this will not work.

   ``Path.__iter__`` is optimized to read the file a small amount at a time, so ``for line in path`` is workable for a textual line-based file format.

- If the loader requires a third-party library, import it inside ``iterload()`` or ``reload()`` (or ``open_<filetype>`` if necessary).
  Do not import at the toplevel, or ``vd`` will fail to start when the library is not installed.
    - preferably, import it using ``modname = importExternal(modname, pythonPackageName``. If the user does not have the package installed, it will output instructions to ``pip3 install pythonPackageName``.

.. autofunction:: visidata.vd.importExternal

By default, a Sheet has one Column which just displays a string representation of the row.
So the above example is a good starting point for any loader; just get the rows however they come most easily from the source, and launch ``vd`` with a sample dataset in that format.
Then use :kbd:`Ctrl+Y` to explore the resulting Python object, to find what attributes to show on the sheet.

reload()
~~~~~~~~

For more control over the whole loading process, ``BaseSheet.reload()`` can be overridden instead of ``iterload()``:

::

        @asyncthread
        def reload(self):
            self.rows = []
            for line in self.source:
                self.addRow([line])

-  ``@asyncthread`` launches the decorated function in its own thread.  See :ref:`Threads<threads>`
-  ``sheet.rows`` must always be reset to a new list.  **Never** call ``sheet.rows.clear()``.
-  Always add rows using :ref:`addRow()<sheets>`.

Supporting asynchronous loaders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Loading a large dataset in the main thread will cause the interface to freeze.
However, the basic TableSheet ``reload`` and ``iterload`` structure results in an :ref:`asynchronous <threads>` loader by default.
Since rows are yielded **one at a time**, they become available as they are loaded, and ``reload`` itself is decorated with an ``@asyncthread``, which causes it to be launched in a new thread.

- All row iterators should be wrapped with :ref:`Progress<progress>`.
  This updates the progress percentage as it passes each element through.

- Do not depend on the order of ``rows`` after they are added; e.g. do not reference ``rows[-1]``.  The order of rows may change during an asynchronous loader.

- Catch any ``Exception`` that might be raised while handling a specific row, and add them as the row instead.  Uncaught exceptions will cause the loader thread to abort.

- Do not use a bare ``except:`` clause or the loader thread will not be cancelable with :kbd:`Ctrl+C`.

Progress and Exception example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

        class FooSheet(Sheet):
            ...
            def iterload(self):
                for bar in Progress(foolib.iterfoo(self.source.open_text())):
                    try:
                        r = foolib.parse(bar)
                    except Exception as e:
                        r = e
                    yield r

Testing for Loader Performance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Test the loader with a very large dataset to make sure that:

-  the first rows appear immediately;
-  the progress percentage is being updated;
-  the loader can be cancelled (with :kbd:`Ctrl+C`).

.. _enumerate-columns:

Step 4. Enumerate the Columns
------------------------------

Each sheet has a ``columns`` attribute with a unique list of ``Column`` objects. Each ``Column`` provides a
different view into the row.

::

        class FooSheet(Sheet):
            rowtype = 'foobits'  # rowdef: foolib.Bar object

            columns = [
                ColumnAttr('name'),  # foolib.Bar.name
                Column('bar', getter=lambda col,row: row.inside[2],
                              setter=lambda col,row,val: row.set_bar(val)),
                Column('baz', type=int, getter=lambda col,row: row.inside[1]*100)
            ]

In general, set ``columns`` as a class member containing a list of
static columns. If the columns aren't known until data is loaded,
reload/iterload can add new columns using :ref:`addColumn() <tablesheet>`.

If the rowdef is a ``list``, and the columns are dynamic, :ref:`SequenceSheet.reload() <other-sheets>` could handle the Column creation.

::

    class FooSheet(SequenceSheet):
        rowtype = 'foobits'  # rowdef: a list, which is a sequence of values

        def iterload(self):
            with foolib.iterfoo(self.source.open_text() as f:
                r = foolib.parse(bar)
                yield r


Column attributes
~~~~~~~~~~~~~~~~~

Columns have several attributes; all except *name* are **optional** arguments to the constructor:

-  *name*: should be a valid Python identifier and unique among the column names on the sheet.  (Otherwise the column cannot be used in an expression.)
-  *type*: can be ``str``, ``int``, ``float``, ``date``, ``currency``, or a custom type.  By default it is ``anytype``, which passes the original value through unmodified.
-  *width*: the initial width for the column. ``0`` means hidden; ``None`` (default) means calculate on first draw.

Column getters can be any function, but many loaders are satisfied with a static list of ``ItemColumn`` (for values in dict and list rowdefs) and/or ``AttrColumn`` (for a members or attributes directly on the row object).
This is dependent on the loader function; some loaders may prefer to do less parsing to load faster, and then the Columns will need to be correspondingly more complicated.

See the :ref:`Columns section <columns>` for a complete API.

Passthrough options
~~~~~~~~~~~~~~~~~~~

Loaders which use a Python library (internal or external) are encouraged to pass its kwargs using ``**options.getall("foo_")`` interface.
For modules like ``csv`` which expose them as kwargs to some function or constructor, this is very easy:

::

        rdr = csv.reader(fp, **csvoptions())

Full Example
~~~~~~~~~~~~

This is a completely functional loader for the ``sas7bdat`` (SAS dataset file) format, thanks to Jared Hobbs' `sas7bdat package <https://bitbucket.org/jaredhobbs/sas7bdat>`__.

::

    from visidata import Sheet, ItemColumn, Progress

    @VisiData.api
    def open_sas7bdat(vd, p):
        return SasSheet(p.base_stem, source=p)

    class SasSheet(Sheet):
        def iterload(self):
            import sas7bdat
            SASTypes = { 'string': str, 'number': float, }

            self.dat = sas7bdat.SAS7BDAT(str(self.source),
                                         skip_header=True,
                                         log_level=logging.CRITICAL)

            self.columns = []
            for col in self.dat.columns:
                self.addColumn(ItemColumn(col.name.decode('utf-8'),
                                         col.col_id,
                                         type=SASTypes.get(col.type, anytype)))

            with self.dat as fp:
                yield from Progress(fp, total=self.dat.properties.row_count)


Guessing Filetypes
==================

When loading a file, VisiData tries to infer its filetype by peeking at the initial lines of the file and guessing from its structure.

``vd.guess_<filetype>(path)`` contains this logic for checking whether a file might be ``<filetype``.

If those structures are not present, the function should return nothing. If they are, the function should return a dictionary with:

- ``filetype`` being the filetype they detect (corresponding to the ``vd.open_<filetype>``)
- ``_likelihood`` (optional) being a number from 0-10, 10 being most likely and 0 meaning a last ditch effort if nothing else will take it
- any other key/values will be set as options on the *Sheet* the ``open_<filetype>`` function returns

`Examples of guess_filetype functions <https://github.com/saulpw/visidata/commit/4743f92bb855cf931d896e65845c549ce6027e2f>`_


::

        @VisiData.api
        def guess_foo(vd, p):
            import foobar
            if p.open_text().read(8).startswith("#Foo"):
                enc = foobar.encoding(p)
                return dict(filetype='foo', foo_encoding=enc)


Savers
=======

A full-duplex loader requires a **saver**.
The saver iterates over all ``rows`` and ``visibleCols``, calling ``getValue``, ``getDisplayValue`` or ``getTypedValue`` as the saving format allows, and saves the results in its format to the given *path*.
Savers should be decorated with ``@VisiData.api`` in order to make them available through the ``vd`` object's scope.

.. autofunction:: visidata.vd.save_txt

-  *p* is a :ref:`visidata.Path <vd-path>` object referencing the file being written to.
-  *sheets* is a list of 1 or more sheets to be saved.

The saver should preserve the column names and translate their types into ``foolib`` semantics, but other attributes on the Columns are generally not saved.

Savers which can handle typed values should use ``Column.getTypedValue``, and displayable savers (like html, markdown, csv) should use ``Column.getDisplayValue`` (which takes into account the column's *fmtstr*).

Example
^^^^^^^

With this example, saving as filetype ``table`` will call the `tabulate library <https://github.com/astanin/python-tabulate>`__ to save the data in any number of text formats, specified by the ``tbl_tablefmt`` option.
(Several built-in savers use ``tabulate`` also, but those savers work a little differently, as each tablefmt is available as a direct save filetype.)

::

    vd.option('tbl_tablefmt', 'simple', 'file format to save with "table" filetype')

    def get_rows(sheet, cols):
        for row in Progress(sheet.rows):
            yield [ col.getDisplayValue(row) for col in cols ]

    @VisiData.api
    def save_table(path, *sheets):
        import tabulate

        with path.open_text(mode='w') as fp:
            for vs in sheets:
                fp.write(tabulate.tabulate(
                    get_rows(vs, vs.visibleCols),
                    headers=[ col.name for col in vs.visibleCols ],
                    **options.getall('tbl_')))

.. _vd-path:

visidata.Path
=============

``visidata.Path`` is a wrapper around Python's builtin ``pathlib.Path`` that can also handle non-filesystem files (URLs, stdin, files within archives).

The ``given`` attribute is new to ``visidata.Path``.
Other functions listed here are wrappers around the equivalent ``pathlib.Path`` functions, with specialized functionality as needed for non-filesystem files.
All other accesses are forwarded to the inner ``pathlib.Path`` object, but will probably not work for non-filesystem files.

.. autoattribute:: visidata.Path.given

.. autofunction:: visidata.Path.exists
.. autofunction:: visidata.Path.open
.. autofunction:: visidata.Path.open_text
.. autofunction:: visidata.Path.read_text
.. autofunction:: visidata.Path.open_bytes
.. autofunction:: visidata.Path.read_bytes
.. autofunction:: visidata.Path.stat
.. autofunction:: visidata.Path.with_name

URL Scheme Loaders
---------------------------------------

When VisiData tries to open a URL with schemetype of ``foo`` (i.e.
starting with ``foo://``), it calls ``openurl_foo(urlpath, filetype)``.
``urlpath`` is a ``UrlPath`` object, with attributes for each of the
elements of the parsed URL.

``openurl_foo`` should return a Sheet or call ``error()``. If the URL
indicates a particular type of Sheet (like ``magnet://``), then it
should construct that Sheet itself. If the URL is just a means to get to
another filetype, then it can call ``openSource`` with a Path-like
object that knows how to fetch the URL:

::

        def openurl_foo(p, filetype=None):
            return openSource(FooPath(p.url), filetype=filetype)
