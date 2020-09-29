Key Columns
-----------

.. autofunction:: visidata.Sheet.setKeys
.. autofunction:: visidata.Sheet.unsetKeys
.. autofunction:: visidata.Sheet.rowkey
.. autofunction:: visidata.Sheet.keystr
.. autodata:: visidata.Sheet.keyCols
.. autodata:: visidata.Sheet.nonKeyVisibleCols

Selected Rows
-------------

Each Sheet has a set of "selected rows", which is a strict subset of the rows on the sheet.

.. autofunction:: visidata.Sheet.selectRow
.. autofunction:: visidata.Sheet.unselectRow
.. autofunction:: visidata.Sheet.isSelected

.. autodata:: visidata.Sheet.nSelected

    - Since selectedRows takes O(nRows) to compute, it is preferable to use nSelected instead of len(selectedRows).
    - Generally, use nRows/nSelected properties instead of calling len() for this reason

.. autodata:: visidata.Sheet.selectedRows
.. autodata:: visidata.Sheet.someSelectedRows
.. autofunction:: visidata.Sheet.select
.. autofunction:: visidata.Sheet.unselect
.. autofunction:: visidata.Sheet.clearSelected
.. autofunction:: visidata.Sheet.deleteSelected
.. autofunction:: visidata.Sheet.selectByIdx
.. autofunction:: visidata.Sheet.unselectByIdx


- ``[un]selectByIdx`` is used by (un)select-regex since vd.searchRegex returns a list of rowid

- To clear the set of selected rows before any bulk selection, set `options.bulk_select_clear` to True.
  The status message will include "instead" as a remind that the option is enabled.

Undo
-------

Command Log and Replay
-----------------------

Sorting
-------

.. autofunction:: visidata.Sheet.orderBy
.. autofunction:: visidata.Sheet.sort

Grouping and Aggregators
------------------------

.. autofunction:: visidata.Sheet.addAggregators
.. autofunction:: visidata.Column.getValueRows
.. autofunction:: visidata.Column.getValues
