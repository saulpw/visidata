Interface
=========

Terminal
--------

.. autofunction:: visidata.BaseSheet.windowWidth
.. autofunction:: visidata.BaseSheet.windowHeight
.. autofunction:: visidata.BaseSheet.refresh
.. autofunction:: visidata.VisiData.redraw
.. autofunction:: visidata.BaseSheet.draw
.. autofunction:: visidata.VisiData.drawall
.. autofunction:: visidata.SuspendCurses

Cursor
------

.. autofunction:: visidata.Sheet.topRowIndex
.. autofunction:: visidata.Sheet.cursorCol
.. autofunction:: visidata.Sheet.cursorColIndex
.. autofunction:: visidata.Sheet.cursorRowIndex
.. autofunction:: visidata.Sheet.cursorCell
.. autofunction:: visidata.Sheet.cursorDisplay
.. autofunction:: visidata.Sheet.cursorTypedValue
.. autofunction:: visidata.Sheet.cursorValue
.. autofunction:: visidata.Sheet.cursorDown
.. autofunction:: visidata.Sheet.cursorRight
.. autofunction:: visidata.Sheet.moveToNextRow
.. autofunction:: visidata.Sheet.moveToCol
.. autofunction:: visidata.Sheet.moveToRow

.. autofunction:: visidata.BaseSheet.checkCursor

Layout
------
.. autofunction:: visidata.Sheet.calcColLayout


Input/Edit
----------

.. autofunction:: visidata.vd.input
.. autofunction:: visidata.vd.confirm
.. autofunction:: visidata.vd.launchEditor
.. autofunction:: visidata.vd.editline
.. autofunction:: visidata.vd.editText
.. autofunction:: visidata.Sheet.editCell

Colors
------
.. autofunction:: visidata.Sheet.addColorizer
.. autofunction:: visidata.Sheet.removeColorizer

Status
------

.. autofunction:: visidata.vd.status
.. autofunction:: visidata.vd.warning
.. autofunction:: visidata.vd.fail

.. autofunction:: visidata.BaseSheet.leftStatus
.. autofunction:: visidata.vd.rightStatus
.. autofunction:: visidata.BaseSheet.statusLine
