Key Columns
-----------

.. autofunction:: visidata.Sheet.setKeys
.. autofunction:: visidata.Sheet.unsetKeys
.. autofunction:: visidata.Sheet.rowkey
.. autofunction:: visidata.Sheet.keystr
.. autoattribute:: visidata.Sheet.keyCols
.. autoattribute:: visidata.Sheet.nonKeyVisibleCols

Selected Rows
-------------

Each Sheet has a set of "selected rows", which is a strict subset of the rows on the sheet.

.. autoattribute:: visidata.Sheet.selectedRows
.. autoattribute:: visidata.Sheet.someSelectedRows
.. autoattribute:: visidata.Sheet.nSelectedRows

.. autofunction:: visidata.Sheet.selectRow
.. autofunction:: visidata.Sheet.unselectRow
.. autofunction:: visidata.Sheet.isSelected

.. autofunction:: visidata.Sheet.clearSelected

.. autofunction:: visidata.Sheet.selectByIdx
.. autofunction:: visidata.Sheet.unselectByIdx

.. autofunction:: visidata.Sheet.select
.. autofunction:: visidata.Sheet.unselect
.. autofunction:: visidata.Sheet.deleteSelected


.. note::

    To clear the set of selected rows before any bulk selection, set ``options.bulk_select_clear`` to True.
    The status message will include "instead" as a reminder that the option is enabled.

.. warning::

    ``selectedRows`` feels like a list, but it's actually a property that iterates over all rows to generate the selected rows in sheet order.
    With large datasets, collecting the list of selected rows itself can take a large time, regardless of the number of rows that are actually selected.
    So instead of using selectedRows in the execstr, call an @asyncthread @Sheet.api function which uses sheet.selectedRows.
    Use it as a parameter immediately or save it to a local variable on the first usage, to avoid unnecessary work.

Undo
-------

.. autofunction:: visidata.addUndo

Sorting
-------

.. autofunction:: visidata.Sheet.orderBy
.. autofunction:: visidata.Sheet.sort
