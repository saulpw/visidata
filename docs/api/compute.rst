====
Computational Engine
====

Cell, Value, DisplayValue
===========================



.. autofunction:: visidata.Column.setCache
.. autofunction:: visidata.Column.getCell
.. autofunction:: visidata.Column.getDisplayValue
.. autofunction:: visidata.Column.format
.. autofunction:: visidata.Column.setValue
.. autofunction:: visidata.Column.setValues

.. autofunction:: visidata.Column.calcValue
.. autofunction:: visidata.Column.getValue

Types
==========================

.. autofunction:: visidata.Column.getTypedValue
.. autofunction:: visidata.Column.setValuesTyped

Null
===========================
.. autofunction:: visidata.BaseSheet.isNullFunc

Errors
==========================

.. autofunction:: visidata.Column.isError
.. autofunction:: visidata.Column.putValue
.. autofunction:: visidata.Column.setValuesFromExpr
.. autofunction:: visidata.Column.recalc

Expressions
==========================

.. autofunction:: visidata.BaseSheet.evalexpr
.. autofunction:: visidata.Sheet.recalc

Clears cache values for entire sheet (calls Column.recalc() for each column).
