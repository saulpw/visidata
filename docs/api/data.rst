Selected Rows
-------------

Each TableSheet has a set of *selected rows*, which is a strict subset of the rows on the sheet.

.. autoattribute:: visidata.TableSheet.selectedRows
.. autoattribute:: visidata.TableSheet.someSelectedRows
.. autoattribute:: visidata.TableSheet.nSelectedRows

.. autofunction:: visidata.TableSheet.selectRow
.. autofunction:: visidata.TableSheet.unselectRow
.. autofunction:: visidata.TableSheet.isSelected

.. autofunction:: visidata.TableSheet.clearSelected

.. autofunction:: visidata.TableSheet.selectByIdx
.. autofunction:: visidata.TableSheet.unselectByIdx

.. autofunction:: visidata.TableSheet.select
.. autofunction:: visidata.TableSheet.unselect
.. autofunction:: visidata.TableSheet.deleteSelected


.. note::

    To clear the set of selected rows before any bulk selection, set ``options.bulk_select_clear`` to True.
    The status message will include "instead" as a reminder that the option is enabled.

.. warning::

    ``selectedRows`` feels like a list, but it's actually a property that iterates over all rows to generate the selected rows in sheet order.
    With large datasets, collecting the list of selected rows itself can take a large time, regardless of the number of rows that are actually selected.
    So instead of using selectedRows in the execstr, call an ``@asyncthread`` ``@TableSheet.api`` function which uses sheet.selectedRows.
    Use it as a parameter immediately or save it to a local variable on the first usage, to avoid unnecessary work.

Sorting
-------

.. autofunction:: visidata.TableSheet.orderBy
.. autofunction:: visidata.TableSheet.sort
