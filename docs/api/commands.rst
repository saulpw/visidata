.. _commands:

Commands
--------

VisiData is **command-driven**, which means that it only does something when you tell it to.
Otherwise, it just sits there, waiting for your next command.

Every command is a discrete unit of behavior that does a defined task and runs to completion.
Functions that could take longer than a couple hundred milliseconds should run in their own thread (see :ref:`Threads <threads>`).

Every command should be **reproducible**: given the same sheet, cursor position, and :ref:`input <input>` string (if relevant), a command should yield identical output (with a few obvious exceptions, like :kbd:random-rows).

Any command which makes changes to a :ref:`saveable sheet<sheets>` is appended to that sheet's **Command Log**.
Since all state changes must be initiated by a reproducible command, this command log can be `replayed </docs/save-restore>`__.

Adding new commands is a natural way to extend VisiData's functionality.

Command Overview
~~~~~~~~~~~~~~~~

Commands and Keybindings are managed in a similar way to options.
The same precedence hierarchy is used, so that commands can be created or overridden for a specific type of sheet, or even a specific sheet itself.

Since all Sheets ultimately inherit from ``BaseSheet``, a command on ``BaseSheet`` is effectively a global command.

.. _command-context:

Command Context
^^^^^^^^^^^^^^^

The *execstr* is a string of Python code passed to ``exec()`` when the command is run.

``exec()`` looks up symbols in this order:

-  the current ``sheet``
-  the ``vd`` object
-  the ``visidata`` module (see ``addGlobals()`` and ``getGlobals()`` :ref:`below<other-commands>`)

The ``vd`` and ``sheet`` symbols are available to specify explicitly.

.. note::

    Unqualified ``options`` in a command execstr will use the sheet-specific options context for the current sheet.

.. warning::

   In an *execstr*, while you can **get** an attribute on ``vd`` or ``sheet`` without specifying the object, to **set** an attribute does require an explicit object.  e.g. instead of ``cursorRowIndex=2``, it must be ``sheet.cursorRowIndex=2``.

Commands API
~~~~~~~~~~~~

.. autofunction:: visidata.BaseSheet.addCommand

Keybindings
~~~~~~~~~~~~

   - Use "``^X``" for :kbd:`Ctrl+X`.
   - Primarily, plugin authors and users should use ``0-9``, "``KEY_F(1)``", ``ALT+`` for custom keybindings; these are purposefully left available for user keybindings.
   - Consider not providing a default at all, for infrequently used commands.
   - Instead give it an easy and memorable longname, and/or a unique *helpstr* which can be searched for in the **Command Help** (:kbd:`g Ctrl+H`) with :kbd:`g/`.
   - Many other keycodes can be returned from the curses library as strings.
   - To discover what to use for some unknown key, press that key in VisiData and use the keystroke shown in the status bar.

.. autoattribute:: visidata.vd.allPrefixes

``vd.allPrefixes`` is a list of *prefixes* (keystrokes that don't trigger the end of a command sequence).
New prefixes can be added to this list, and then they can also be used as prefixes in keybindings.

.. note::

    Combinations of prefixes are allowed, but only in the specified order: ``g`` must come before ``z``, which must come before ``ALT``.

.. note::

    ``ALT`` is a just a handy constant for "``^[``", which represents :kbd:`Ctrl+[`, which maps to :kbd:`Esc` in the terminal.
    Curses represents :kbd:`Alt+X` (:kbd:`Meta+X` on some keyboards) as :kbd:`Esc x`. So to bind a command to :kbd:`Alt+X`, use ``ALT+'x'`` or ``'^[x'``.

.. _other-commands:

Other helpful functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: visidata.vd.bindkey
.. autofunction:: visidata.BaseSheet.bindkey
.. autofunction:: visidata.BaseSheet.execCommand
.. autofunction:: visidata.addGlobals
.. autofunction:: visidata.getGlobals

Rules for command longnames
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1) 3 words max, 2 words if possible.  A longname should be short and fit on a keymap.

2) Command classes should be unique in their first 3 chars and ideally mostly in their first 2.

3) Command longnames should be intuitively understandable, or at least not jargony.

4) Longnames should evoke interface, when possible.

5) Use existing verb-object-input structure if possible:

Verbs:

-  ``open``: push new sheet
-  ``jump``: push existing sheet
-  ``dup``: push copy of sheet
-  ``show``: display on status
-  ``go``: move the cursor
-  ``scroll``: change the visible screen area without changing the cursor
-  ``addcol``: add new column to this sheet
-  ``setcol``: set selected cells in this column
-  ``search``: search one or more columns
-  ``searchr``: search reverse
-  ``select/unselect/stoggle``: add/remove rows from selected rows
-  ``syscopy/syspaste``: copy/paste to system clipboard
-  ``sysopen``: open with $EDITOR or other external program

Objects:

- ``-all``: all sheets or all visible columns
- ``-col``: cursorCol
- ``-cols``: all visible columns
- ``-cells``: this column, selected rows
- ``-selected``: selected rows

Inputs:

- ``-expr``: python expression
- ``-regex``: python regex

Many others are used, see the full command list for inspiration.

Examples
~~~~~~~~

::

    def show_hello(sheet):
        vd.status(sheet.options.disp_hello)

    # `sheet` members and `vd` members are available in the execstr scope
    BaseSheet.addCommand(None, 'show-hello', 'show_hello()', 'show a warm greeting')

    # bind Shift+H, Ctrl+H, and Alt+H to this command
    BaseSheet.bindkey('H', 'show-hello')
    BaseSheet.bindkey('^H', 'show-hello')
    BaseSheet.bindkey(ALT+'h', 'show-hello')
