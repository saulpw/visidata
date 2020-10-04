===============
Modifying Data
===============

Foundation of Modify
=====================

There are three frames for data modification within VisiData:
* modifying cell values
* deleting rows
* adding rows

.. autofunction:: visidata.Sheet.editCell
.. autofunction:: visidata.Sheet.deleteBy
.. autofunction:: visidata.TableSheet.newRow
.. autofunction:: visidata.TableSheet.addNewRows


Deferred Modification
======================

On sheets where changes go straight to source, like **SQLite** and **DirSheet**, modifications would be bad to make right away. For these cases, they are deferred, Modifications are cached and coloured, until they are committed to with explicit user save (``z Ctrl+S``).

Most sheets can add deferring by setting ``Sheet.defer = True``, but they may have to implement their own ``Sheet.putChanges``.

.. autofunction:: visidata.Sheet.preloadHook
.. autofunction:: visidata.Column.getSavedValue

.. autofunction:: visidata.Sheet.rowAdded
.. autofunction:: visidata.Sheet.rowDeleted
.. autofunction:: visidata.Column.cellChanged

.. autofunction:: visidata.Sheet.isDeleted
.. autofunction:: visidata.Sheet.isChanged

.. autofunction:: visidata.Sheet.commitAdds
.. autofunction:: visidata.Sheet.commitDeletes
.. autofunction:: visidata.Sheet.commitMods

.. autofunction:: visidata.Sheet.commit
.. autofunction:: visidata.Sheet.getDeferredChanges
.. autofunction:: visidata.Sheet.changestr
.. autofunction:: visidata.Sheet.putChanges

Example
~~~~~~~~

.. note::

    ``Sheet.editCell`` requires *indexes* for its parameters.
    ``sheet.cursorColIndex`` and ``sheet.cursorRowIndex`` are examples of within sheet index properties that can be passed to ``Sheet.editCell``.

::

    Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); options.cmd_after_edit and sheet.execCommand(options.cmd_after_edit)', 'edit contents of current cell')


::

    sheet.deleteBy(sheet.isSelected)

::

    sheet.addRow(row)


