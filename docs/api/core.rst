Sheets
====================================

.. data:: visidata.vd.sheets

The list of active sheets, generally treated as a stack.  The first item (0) is always the top displayed sheet.

.. autofunction:: visidata.vd.getSheet
.. autofunction:: visidata.vd.push
.. autofunction:: visidata.vd.replace
.. autofunction:: visidata.vd.remove
.. autofunction:: visidata.vd.quit

.. autofunction:: visidata.vd.openPath
.. autofunction:: visidata.vd.openSource

.. autofunction:: visidata.vd.saveSheets

The Sheet class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: visidata.BaseSheet.reload
.. autofunction:: visidata.Sheet.iterload

.. autofunction:: visidata.BaseSheet.ensureLoaded

.. data:: visidata.BaseSheet.name

.. autofunction:: visidata.BaseSheet.__copy__
.. autofunction:: visidata.BaseSheet.__len__
.. data:: visidata.BaseSheet.cmdlog
.. data:: visidata.BaseSheet.cmdlog_sheet

.. data:: visidata.TableSheet.columns
.. data:: visidata.TableSheet.nCols
.. autofunction:: visidata.TableSheet.addColumn
.. data:: visidata.TableSheet.visibleCols
.. data:: visidata.TableSheet.nVisibleCols
.. autofunction:: visidata.TableSheet.column

.. data:: visidata.TableSheet.rows
.. data:: visidata.TableSheet.nRows
.. data:: visidata.TableSheet.visibleRows
.. data:: visidata.TableSheet.nVisibleRows

.. autofunction:: visidata.TableSheet.openRow

.. autofunction:: visidata.TableSheet.gatherBy
.. autofunction:: visidata.TableSheet.rowid

.. autofunction:: visidata.TableSheet.openCell
.. autofunction:: visidata.TableSheet.iterrows


   - rows are not hashable and can't be looked up easily by content without linear (and expensive) search.
   - But id(obj) is a hashable integer which is guaranteed to be unique and constant for this object during its lifetime.
   - We store id(row) as the keys in a dict pointing to the row itself (is this convenience used?)
   - this makes selection/unselection and checking for selection, have the same cost as set add/remove/check
   - select/unselect/stoggle all are now O(n log n), whereas they could have been O(n) if selection were in e.g. a parallel array, or an attribute on the row.


Sheet class hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: visidata.BaseSheet
.. autoclass:: visidata.TableSheet
.. autoclass:: visidata.IndexSheet
.. autoclass:: visidata.TextSheet
.. autoclass:: visidata.SequenceSheet
.. autoclass:: visidata.PyobjSheet

.. note::

    ``PyobjSheet`` can be passed any Python object and will return specialized subclasses for lists of objects, namedtuples, and dicts.
