.. _sheets:

Sheets
====================================

A Sheet is a representation of some source, usually a Path.
A path can be opened, returning a sheet, and/or a sheet can be saved to path.

.. autofunction:: visidata.vd.openPath
.. autofunction:: visidata.vd.openSource

.. autofunction:: visidata.vd.saveSheets

Sheets API
---------

.. autoclass:: visidata.BaseSheet

.. autoattribute:: visidata.BaseSheet.name

.. autofunction:: visidata.BaseSheet.__len__
.. autofunction:: visidata.BaseSheet.__copy__

.. autofunction:: visidata.BaseSheet.reload

TableSheet
^^^^^^^^^^^

Sheets are generally specialized for their rowtype, and TableSheet, used for sheets with rows and columns, is the most common base class.
(So common, that it was originally just called ``Sheet``.  For clarity, ``TableSheet`` is preferred, but ``Sheet`` is a valid alias that will never be deprecated.)

.. autoclass:: visidata.TableSheet

.. data:: visidata.TableSheet.rows

List of row objects on this sheet.

.. data:: visidata.TableSheet.columns

List of all Column objects on this sheet (including hidden columns).


.. autoattribute:: visidata.TableSheet.nRows
.. autoattribute:: visidata.TableSheet.nCols

.. autoattribute:: visidata.TableSheet.visibleCols
.. autoattribute:: visidata.TableSheet.nVisibleCols

.. autofunction:: visidata.TableSheet.addRow
.. autofunction:: visidata.TableSheet.addColumn

.. autofunction:: visidata.TableSheet.iterload

.. autofunction:: visidata.TableSheet.rowid
.. autofunction:: visidata.TableSheet.column

.. autofunction:: visidata.TableSheet.openRow
.. autofunction:: visidata.TableSheet.openCell
.. autofunction:: visidata.TableSheet.gatherBy

Other Common Sheet Types
^^^^^^^^^^^^^^^^^^^^^^^^^^

These can be used as base classes, or instantiated as they are, or used as templates for rows with similar structure,

.. autoclass:: visidata.IndexSheet
.. autoclass:: visidata.TextSheet
.. autoclass:: visidata.SequenceSheet
.. autoclass:: visidata.PyobjSheet

The Sheet Stack
-----------------

.. data:: visidata.vd.sheets

The "sheet stack", a list of active sheets (available as the **Sheets Sheet** via :kbd:`Shift+S`).
The top sheet, or the displayed sheet, is the first item in the list (``vd.sheets[0]``).

.. autofunction:: visidata.vd.push
.. autofunction:: visidata.vd.replace
.. autofunction:: visidata.vd.remove
.. autofunction:: visidata.vd.quit

.. autofunction:: visidata.vd.getSheet

