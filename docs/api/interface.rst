Interface
=========

Terminal
--------

.. autodata:: visidata.BaseSheet.windowWidth
.. autodata:: visidata.BaseSheet.windowHeight
.. autofunction:: visidata.BaseSheet.refresh
.. autofunction:: visidata.VisiData.redraw
.. autofunction:: visidata.BaseSheet.draw
.. autofunction:: visidata.VisiData.drawall
.. autofunction:: visidata.SuspendCurses

Cursor
------

.. autodata:: visidata.Sheet.topRowIndex
.. autodata:: visidata.Sheet.cursorCol
.. autodata:: visidata.Sheet.cursorColIndex
.. autodata:: visidata.Sheet.cursorRowIndex
.. autodata:: visidata.Sheet.cursorCell
.. autodata:: visidata.Sheet.cursorDisplay
.. autodata:: visidata.Sheet.cursorTypedValue
.. autodata:: visidata.Sheet.cursorValue
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
.. autodata:: visidata.BaseSheet.statusLine
