===============
Modifying Data
===============

Foundation of Modify
=====================

There are three frames for data modification within VisiData:

* adding rows
* deleting rows
* modifying cell values

.. autofunction:: visidata.TableSheet.newRow
.. autofunction:: visidata.TableSheet.addNewRows
.. autofunction:: visidata.Sheet.editCell
.. autofunction:: visidata.Sheet.deleteBy

Undo
-------

When a function adds, removes, or modifies data--including metadata--as part of a user action, it needs to ensure that operation is **undoable**.
For many operations, this is already handled internally by existing functions.
For instance, if the user executes a command which modifies cell values via ``Column.setValues``, the ``undo`` command will undo those modifications automatically.

If a new operation changes the data or metadata and undo is not already handled by existing functionality, then the new operation needs to call ``addUndo()`` to add an *undo function* to the currently executing command.

For performance reasons, undo functions should generally be as large as possible.
For instance, ``Column.setValues`` adds a single undo function to undo all changes in one go.
By contrast, ``Column.setValue`` does not add an undo function at all.
Therefore, commands should always use ``Column.setValues``, unless for some special reason the modification should not be undoable.
Undo functions, however, should use ``Column.setValue``, so it doesn't add an undo function for the undo itself.
(Redo is handled by replaying the previous command, not by undoing the undo).

.. autofunction:: visidata.addUndo


Deferred Modification
======================

On sheets where ``putValue`` changes the source directly, like **SQLite** and **DirSheet**, it would be undesirable for modifications to happen immediately.
For these cases, the modifications are cached, shown visually on the sheet in a different color, and deferred until they are committed with an explicit ``commit-sheet`` (bound to :kbd:`z Ctrl+S`).

Sheet types can add this deferring behavior by setting their ``defer`` attribute to ``True`` (either on the class type or on the individual sheet instance), but they may have to implement their own ``Sheet.putChanges``.

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
--------

.. note::

    ``Sheet.editCell`` requires row and column *indexes* for its parameters.
    For example, ``cursorVisibleColIndex`` and ``cursorRowIndex`` are sheet attributes that can be passed to ``Sheet.editCell``.

::

    Sheet.addCommand('e', 'edit-cell',
                     'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex))',
                     'edit contents of current cell')


::

    # equivalent to Sheet.deleteSelected but slower
    sheet.deleteBy(sheet.isSelected)

::

    sheet.addRow(row)

