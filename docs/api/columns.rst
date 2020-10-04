.. _columns:

Columns
====================================

Columns are the heart of the VisiData computation engine.

Each column can **calculate** a value from a row object; and it might also be able to **put** a different value into the row object (for a later calculate to re-derive).

A Column subclass can override ``calcValue`` and ``putValue`` to define its fundamental interaction with the row object.
This is often the only thing a Column subclass has to do.

``calcValue`` and ``putValue`` should generally not be called by application code.
Instead, apps and plugins should call ``getValue`` and ``setValue``, which provide appropriate layers of caching.

.. autoclass:: visidata.Column
.. autoattribute:: visidata.Column.name
.. autoattribute:: visidata.Column.type
.. autoattribute:: visidata.Column.width
.. autoattribute:: visidata.Column.fmtstr

.. autoattribute:: visidata.Column.hidden

.. autofunction:: visidata.Column.calcValue
.. autofunction:: visidata.Column.putValue

.. autofunction:: visidata.Column.getValue
.. autofunction:: visidata.Column.getTypedValue
.. autofunction:: visidata.Column.getDisplayValue
.. autofunction:: visidata.Column.formatValue

.. autofunction:: visidata.Column.getValueRows
.. autofunction:: visidata.Column.getValues


.. autofunction:: visidata.Column.setValue
.. autofunction:: visidata.Column.setValues
.. autofunction:: visidata.Column.setValuesTyped
.. autofunction:: visidata.Column.setValuesFromExpr

.. autofunction:: visidata.BaseSheet.evalExpr
.. autofunction:: visidata.Column.recalc
.. autofunction:: visidata.TableSheet.recalc
.. autofunction:: visidata.Column.isError

- ``calcValue`` may be arbitrarily expensive or even asynchronous, so once the value is calculated, it is cached until ``Column.recalc()`` is called.
- ``putValue`` may modify the source data directly (for instance, if the row object represents a row in a database table).  VisiData will *never* modify source data without an explicit ``save`` command.  So applications (and all other code) must call ``setValue`` to change the value of any cell.

- ``delete-cell`` actually just calls setValue with None.


Column Subclasses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: visidata.ItemColumn
.. autoclass:: visidata.AttrColumn
.. autoclass:: visidata.ExprColumn
.. autoclass:: visidata.SettableColumn
.. autoclass:: visidata.SubColumnFunc

Types
======

The value returned by getValue could be many different things:

   - a string
   - numerically typed
   - a list or dict
   - None
   - a null value (according to ``options.null_value``)
   - an Exception (error getting)
   - a Thread (async pending)
   - any python object

This value may need to be parsed and/or converted to a consistent type.
So, every column has a ``type`` attribute, which affects how it is parsed, displayed, grouped, sorted, and more.

The default column type is ``anytype``, which lets the underlying value pass through unaltered.
This is the only ``type`` for which ``Column.getTypedValue`` can return arbitrary types.

The classic VisiData column types are:

============  ==================  =========  =================  ============
type          description         numeric    command            keystrokes
============  ==================  =========  =================  ============
``anytype``   pass-through                   ``type-anytype``   :kbd:`z~`
``str``       string                         ``type-str``       :kbd:`~`
``date``      date/time           Y          ``type-date``      :kbd:`@`
``int``       integer             Y          ``type-int``       :kbd:`#`
``float``     decimal             Y          ``type-float``     :kbd:`%`
``currency``  decimal with units  Y          ``type-currency``  :kbd:`$`
``vlen``      sequence length     Y          ``type-vlen``      :kbd:`z#`
============  ==================  =========  =================  ============

The default keybindings for setting types are all on the shifted top left keys on a US keyboard.

User-defined Types
~~~~~~~~~~~~~~~~~~~

Fundamentally, a type is a function which takes the underlying value and returns an object of a specific type.
This function should accept a string and do a reasonable conversion, like Python ``int`` and ``float`` do.
And like those builtin types, this function should produce a reasonable baseline zero (arithmetic identity) when passed no parameters or None.

Computations should generally call ``getTypedValue``, so that the values being used are consistently typed.

If the underlying value is None, the result will be a ``TypedWrapper``, which provides the baseline zero value for purposes of comparison, but a stringified version of the underlying value for display.
For a ``calcValue`` which raises or returns an Exception, ``getTypedValue`` will return a ``TypedExceptionWrapper`` with similar behavior.


In the following, ``TYPE`` is the type (like ``int``, ``date``, etc), and ``typedval`` is an instance of that type.

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
    - idempotent (``TYPE(TYPE(v)) == TYPE(v)``)

.. autoclass:: visidata.vd.addType

Nulls
~~~~~~

VisiData has a crude concept of null values.  These interact with:
   a. aggregators: the denominator counts only non-null values
   b. the Describe Sheet: only null values count in the nulls column
   c. the ``fill-nulls`` command
   d. the ``melt`` command only keeps non-null values
   e. the ``prev-null`` and ``next-null`` commands (:kbd:`z<` and :kbd:`z>`)

- The null values are Python ``None`` and options.null_value if set.

.. note::

    ``options.null_value`` can be used to specify a null value in addition to Python ``None``.
    The CLI can only set this option to a string like ``''`` (empty string) or ``'NA'``.
    The option can be set to a different type in ``.visidatarc`` or other code, though:

    ::

        options.null_value = 0.0
        options.null_value = date("1980-01-01")

.. autofunction:: visidata.BaseSheet.isNullFunc

There is no direct isNull function, because the possible null values can change at runtime via the above option, and getting an option value is very expensive to do in a bulk operation.

Aggregators
===========

Aggregators allow you to gather the rows within a single column, and interpret them using descriptive statistics.
VisiData comes pre-loaded with a default set like mean, stdev, and sum.

.. autofunction:: visidata.Sheet.addAggregators

.. autofunction:: visidata.vd.aggregator

The `type` parameter is optional. It allows you to define the default type of the aggregated column.

Example
~~~~~~~

Add aggregator for :ref:`numpy's internal rate of return <https://numpy.org/devdocs/reference/generated/numpy.irr.html>`__ module:

```
import numpy as np
vd.aggregator('irr', np.irr, type=float)
```
