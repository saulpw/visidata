Columns
====================================

Columns are the heart of the VisiData calculation engine.

Each column can **calculate** a value from a row object; and it might also be able to **put** a different value into the row object (for a later calculate to re-derive).

A Column subclass can override ``calcValue`` and ``putValue`` to define its fundamental interaction with the row object.
This is often the only thing a Column subclass has to do.

``calcValue`` and ``putValue`` should generally not be called by application code.
Instead, apps and plugins should call ``getValue`` and ``setValue``, which provide appropriate layers of caching.

.. data:: visidata.Column.name
.. data:: visidata.Column.type
.. data:: visidata.Column.width
.. data:: visidata.Column.fmtstr
.. data:: visidata.Column.expr

.. autofunction:: visidata.Column.setWidth()

.. autodata:: visidata.Column.hidden

.. autofunction:: visidata.Column.calcValue
.. autofunction:: visidata.Column.putValue

.. autofunction:: visidata.Column.getValue
.. autofunction:: visidata.Column.getValueRows
.. autofunction:: visidata.Column.getValues
.. autofunction:: visidata.Column.getTypedValue
.. autofunction:: visidata.Column.getDisplayValue

.. autofunction:: visidata.Column.format

.. autofunction:: visidata.Column.setValue
.. autofunction:: visidata.Column.setValues
.. autofunction:: visidata.Column.setValuesTyped
.. autofunction:: visidata.Column.setValuesFromExpr

.. autofunction:: visidata.Column.setCache

.. autofunction:: visidata.BaseSheet.evalexpr
.. autofunction:: visidata.Column.recalc
.. autofunction:: visidata.TableSheet.recalc
.. autofunction:: visidata.Column.isError

.. autofunction:: visidata.Sheet.addAggregators
If a Column should be cached, prefer to specify *cache* in the constructor instead of using setCache.

- ``calcValue`` may be arbitrarily expensive or even asynchronous, so once the value is calculated, it is cached until ``Column.recalc()`` is called.
- ``putValue`` may modify the source data directly (for instance, if the row object represents a row in a database table).  VisiData will *never* modify source data without an explicit ``save`` command.  So applications (and all other code) must call ``setValue`` to change the value of any cell.

- ``delete-cell`` actually just calls setValue with None.

Types
======

Every column has a ``type``, which affects how it is parsed, displayed, grouped, sorted, and more.
The classic VisiData column types are:

|type    |description    |numeric  |command    |keystrokes    |mnemonic                             |
|--------|---------------|---------|-----------|--------------|-------------------------------------|
|str     |string         |         |type\-str  |~             |looks like a little piece of string  |
|date    |date/time in any decipherable format|Y        |type\-date |@             |"at" sign                            |
|int     |integer        |Y        |type\-int  |\#            |"number" sign                        |
|float   |decimal        |Y        |type\-float|%             |"percent" sign                       |
|currency|decimal with leading or trailing characters, and parsed according to locale|Y        |type\-currency|$             |"dollar" sign                        |
|vlen    |size of a container, or length of a string|Y        |type\-vlen |z\#           |much like an "integer", but specifically for size|
|anytype |default generic type|         |type\-anytype|z~            |even more generic than a string      |

Note that all types except `anytype` and `str` are considered numeric.

{mnemonic}
The keybindings for settings types are in a row on the shifted top left keys on a US QWERTY keyboard.


The core value behind any given cell could be:
   - a string
   - numerically typed
   - a list or dict
   - None
   - a null value (according to ``options.null_value``)
   - an Exception (error getting)
   - a Thread (async pending)
   - any python object

This core value may need to be converted to a consistent type, necessary for sorting, numeric binning, and more.

The default column type is ``anytype``, which lets the underlying value pass through unaltered; this is the only type for which a column can have typed values of arbitrary types.

The user can set the type of a column, which is a function which takes the underlying value and returns a specific type.  This function should accept a string and do a reasonable conversion, like Python ``int`` and ``float`` do.
And like those builtin types, this function should produce a reasonable baseline arithmetic identity when passed no parameters (or None).

Applications should generally call getTypedValue, so that the value they get is consistently typed.

If the underlying value is None, the result will be a TypedWrapper, which provides the baseline value
for purposes of comparison, but a stringified version of the underlying value for display.
For a `calcValue` which raises or returns an Exception, getTypedValue will return a TypedExceptionWrapper with similar behavior.

      - type.formatter(fmtstr, typedval)


Nulls
-------

- The null values are Python ``None`` and options.null_value if set.

- Null values interact with:
   a. aggregators: the denominator counts only non-null values
   b. the Describe Sheet: only null values count in the nulls column
   c. the `fill-nulls` command
   d. the `melt' command only keeps non-null values
   e. the `prev-null` and `next-null` commands (`z<` and `z>`)

options.null_value
^^^^^^^^^^^^^^^^^^^

This option can be used to specify a null value in addition to Python `None`.  This value is typed, so can be set to ``''`` (empty string) or another string (like ``'NA'``), or a number like ``0`` or ``0.0``.

.. autofunction:: visidata.BaseSheet.isNullFunc

There is no direct isNull function, because the possible null values can change at runtime, and getting an option value is very expensive to do in a bulk operation.

User-defined Types
^^^^^^^^^^^^^^^^^^^

``TYPE`` is the type (like `int`, `date`, etc), and ``typedval`` is an instance of that type.

A VisiData type function or constructor must have certain properties:

    - ``TYPE()`` must return a reasonable default value for *TYPE*.
    - ``TYPE(typedval)`` must return an exact copy of *typedval*.
    - ``TYPE(str)`` must convert from a reasonable string representation into *TYPE*.
    - ``TYPE.__name__`` must be set to the official name of the type function or constructor.

Objects returned by ``TYPE(...)`` must be:

- comparable (for sorting)
- hashable
- formattable
- roundable (if numeric, for binning)
- idempotent (TYPE(TYPE(v)) == TYPE(v))

.. autoclass:: visidata.vdtype

- ``.typetype``: actual type class *TYPE* above
- ``.icon``: unicode character in column header
- ``.fmtstr``: format string to use if fmtstr not given
- ``.formatter(fmtstr, typedvalue)``: formatting function (by default `locale.format_string` if fmtstr given, else `str`)

Cells
^^^^^

.. autofunction:: visidata.Column.getCell

Return the DisplayWrapper, the whole kit'n'caboodle used directly by Sheet.draw()

.. autoclass:: visidata.DisplayWrapper

- value: underlying value, before typing
- display: formatted to be displayed directly in the cell (including space
- note: one-character visual tag for the cell
- notecolor: `color_foo` applied to the note
- error: list of strings (a stack trace)

Column Subclasses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: visidata.ItemColumn
.. autoclass:: visidata.AttrColumn
.. autoclass:: visidata.ExprColumn
.. autoclass:: visidata.SettableColumn
.. autoclass:: visidata.SubColumnFunc
