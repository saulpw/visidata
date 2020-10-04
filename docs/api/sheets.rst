.. _sheets:

Sheets
====================================

BaseSheet is a base class defining the interface for Sheets of all kinds.

Sheets are generally specialized for their rowtype, and TableSheet, used for sheets with rows and columns, is the most common base class.
(So common, that it was originally just called ``Sheet``.  For clarity, ``TableSheet`` is preferred, but ``Sheet`` is a valid alias that will never be deprecated.)

.. autoclass:: visidata.BaseSheet
.. autoattribute:: visidata.BaseSheet.name

.. autofunction:: visidata.BaseSheet.__len__
.. autofunction:: visidata.BaseSheet.__copy__

.. autofunction:: visidata.BaseSheet.reload

TableSheet
~~~~~~~~~~~

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

Other Sheets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: visidata.IndexSheet
.. autoclass:: visidata.TextSheet
.. autoclass:: visidata.SequenceSheet
.. autoclass:: visidata.PyobjSheet

The Sheet Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "sheet stack" is the list of active sheets (vvailable via :kbd:`Shift+S`).
The top sheet (the displayed sheet) is the first item (``vd.sheets[0]``) in the list.

.. data:: visidata.vd.sheets

.. autofunction:: visidata.vd.push
.. autofunction:: visidata.vd.replace
.. autofunction:: visidata.vd.remove
.. autofunction:: visidata.vd.quit

.. autofunction:: visidata.vd.getSheet

.. autofunction:: visidata.vd.openPath
.. autofunction:: visidata.vd.openSource

.. autofunction:: visidata.vd.saveSheets
