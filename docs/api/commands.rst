Commands
--------

VisiData is *command-driven*, which means that it only does something
when you tell it to. Otherwise, it just sits there, waiting for your
next command.

Every command is a discrete unit of behavior that does a defined task
and runs to completion. Functions that could take longer than a couple
hundred milliseconds, execute via [@asyncthread](), and provide
`Progress <>`__ which is shown in the `righthand status <>`__.

Every command should be **reproducible**: given the same sheet, cursor
position, and possibly `input <>`__ string, a command should yield
identical output (with a few obvious exceptions, like ``random-rows``).

Any command which makes changes to the `saveable sheet <>`__ is appended
to its `command log <>`__. Since all state changes must be initiated by
a reproducible command, this command log can be `replayed <>`__.

This command log is also used for certain other features, like
undo/redo.

Adding new commands is a natural way to extend VisiData's functionality.

Command Overview
~~~~~~~~~~~~~~~~

Commands (and Keybindings) are managed in a similar way to options. The
same precedence hierarchy is used, so that commands can be created or
overridden for a specific type of sheet, or even a specific sheet
itself.

There are no 'global' commands; however, since all Sheets ultimately
inherit from BaseSheet, a command on BaseSheet is effectively a global
command.

Command Context
^^^^^^^^^^^^^^^

The "execstr" is a string of Python code to ``exec()`` when the command
is run.

``exec()`` looks up symbols in this order:

-  the current ``sheet``
-  the ``vd`` object
-  visidata module (see ``addGlobals`` and ``getGlobals`` below)

The ``vd`` and ``sheet`` symbols are available to specify explicitly.

Notes:

-  In an "execstr", setting attributes on vd and sheet requires an
   explicit object; e.g., instead of ``cursorColIndex=2``, it must be
   ``sheet.cursorColIndex=2``
-  Unqualified ``options`` in command execstr will use the
   sheet-specific options context for the current sheet.

API
~~~

:# BaseSheet.addCommand

-  classmethod; call with a SheetType or a Sheet
-  ``binding``

   -  a string of keystrokes, including **prefixes**.

      -  ``vd.allPrefixes`` is list of "prefixes", or keystrokes that
         don't trigger keybinding lookups.
      -  combinations of prefixes are allowed, but only in the specified
         order: ``g`` must come before ``z``, which must come before
         ``ALT``.
      -  ``ALT`` is a "prefix", because it's actually ``^[`` or ESC; and
         Python curses represents Alt+X (Meta+X on some keyboards) as
         ``^[x``. So the binding is ``ALT+'X'``

   -  Use ``^X`` for Ctrl+X.
   -  Many other keycodes will be returned from the curses library as
      ascii strings.
   -  To discover what to use for some unknown key, press that key in
      VisiData and use the keystroke shown in the status bar.
   -  Primarily, plugin authors and users should use 0-9, KEY\_F\*, ALT+
      for custom keybindings; these are purposefully left available for
      user keybindings.
   -  Consider not providing a default at all, for infrequently used
      commands. Instead give it a memorable name, and/or a unique
      helpstr which you can search for the `command list <>`__
      (``g Ctrl+H``) with ``g/``.

-  ``longname``

   -  use existing structure if possible:

      -  'addcol-' for commands that add a column;
      -  'open-' for commands that push a new sheet;
      -  'go-' for commands that move the cursor;
      -  etc

-  ``execstr``

   -  a Python statement to be ``exec()``'ed when the command is
      executed.

-  ``helpstr`` Shown in **Commands Sheet**.

:# BaseSheet.bindkey

Bind ``longname`` as the command to run when ``keystrokes`` are pressed
on the given ``<SheetType>``.

:# BaseSheet.unbindkey

Unbind ``keystrokes`` on a ``<SheetType>``. May be necessary to avoid a
warning when overriding a binding on the same exact class.

:# BaseSheet.execCommand Execute ``cmd`` in the context of the sheet.
``cmd`` can be a longname, a keystroke, or a Command object.

:# vd.addGlobals Update the visidata globals dict with items from ``g``,
which is a mapping of names to functions.

:# vd.getGlobals

Return the visidata globals dict.

Command longname design guidelines
----------------------------------

1) 3 words max, 2 words if possible. should be short and fit on a keymap
   (verb - object - input)

2) command classes should be unique in their first 3 chars and ideally
   mostly in their first 2.

3) command longnames should be intuitively understandable, or at least
   not jargony

4) longnames should evoke interface, when possible

Verbs:

-  open: push new sheet
-  jump: push existing sheet
-  dup: push copy of sheet
-  show: display on status
-  go: move the cursor
-  scroll: change the visible screen area without changing the cursor
-  addcol: add new column to this sheet
-  setcol: set selected cells in this column
-  search: search one or more columns
-  searchr: search reverse
-  select/unselect/stoggle: add/remove rows from selected rows
-  syscopy/syspaste: copy/paste to system clipboard
-  sysopen: open with $EDITOR or other external program

Nouns: - -expr: python expression - -regex: python regex - -all: all
sheets or all visible columns - -col: cursorCol - -cols: all visible
columns - -cells: this column, selected rows - -selected: selected rows

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

    # unbind keystrokes defined by subclasses, or else they will be overridden
    Sheet.unbindkey('H', 'show-hello')
    Sheet.unbindkey('^H', 'show-hello')
