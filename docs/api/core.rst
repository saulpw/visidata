VisiData, Sheet, and Column objects
====================================

The ``vd`` singleton
~~~~~~~~~~~~~~~~~~~~~~~~~

The VisiData class is a singleton object, containing all of VisiData's global functions and state for the current session.
This object should always be available as ``vd``.

Calling conventions
~~~~~~~~~~~~~~~~~~~

When calling functions on ``vd`` or ``sheet`` outside of a Command *execstr*, they should be properly qualified:

::

    @Sheet.api
    def show_hello(sheet):
        vd.status(sheet.options.disp_hello)

    BaseSheet.addCommand(None, 'show-hello', 'show_hello()')

The current **Sheet** and the **VisiData** object are both in scope for `execstrs <commands#execstr>`__, so within an *execstr*, the ``sheet.`` or ``vd`` may be omitted:

::

    BaseSheet.addCommand(None, 'show-hello', 'status(options.disp_hello)')


Opening, Loading, and Saving Sheets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: visidata.vd.openPath
.. autofunction:: visidata.vd.openSource
.. autofunction:: visidata.BaseSheet.reload
.. autofunction:: visidata.Sheet.iterload

.. autofunction:: visidata.BaseSheet.ensureLoaded

.. autofunction:: visidata.vd.saveSheets

The Sheet Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. data:: visidata.vd.sheets
.. autofunction:: visidata.vd.getSheet
.. autofunction:: visidata.vd.push
.. autofunction:: visidata.vd.replace
.. autofunction:: visidata.vd.remove
.. autofunction:: visidata.vd.quit

The Sheet class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
.. autofunction:: visidata.TableSheet.addRow
.. data:: visidata.TableSheet.visibleRows
.. data:: visidata.TableSheet.nVisibleRows

.. autofunction:: visidata.TableSheet.newRow
.. autofunction:: visidata.TableSheet.addNewRows
.. autofunction:: visidata.TableSheet.openRow

.. autofunction:: visidata.TableSheet.gatherBy
.. autofunction:: visidata.TableSheet.rowid

.. autofunction:: visidata.TableSheet.openCell
.. autofunction:: visidata.TableSheet.iterrows

Sheet class hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: visidata.BaseSheet
.. class:: visidata.TableSheet
.. class:: visidata.IndexSheet
.. class:: visidata.TextSheet
.. class:: visidata.SequenceSheet
.. class:: visidata.PyobjSheet

    - can be passed any python object; special subclasses for list of objects, namedtuples, or dicts

Column
~~~~~~~

.. data:: visidata.Column.type
.. data:: visidata.Column.width
.. data:: visidata.Column.fmtstr
.. data:: visidata.Column.expr

.. autofunction:: visidata.Column.setWidth()

.. autofunction:: visidata.Column.hide()
.. data:: visidata.Column.hidden

Column Subclasses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: visidata.ItemColumn
.. autoclass:: visidata.AttrColumn
.. autoclass:: visidata.ExprColumn
.. autoclass:: visidata.SettableColumn
.. autoclass:: visidata.SubColumnFunc
