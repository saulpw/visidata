Guides
=======

A Guide is an in-app writeup of a particular feature that gives a basic synopsis of how to use it and explains how it works together with other features.

Open the Guide Index with ``Space open-guide-index`` within VisiData or ``vd -P open-guide-index`` from the CLI.


.. note::

    Guides that have not been written yet are grayed out.
    We love to get help with documentation, please get in touch if you want to write one or have other suggestions!

Here's an outline for adding a guide, with our writing style preferences:

1. Launch **GuideIndex** and find the ``name`` of the guide.
2. Create a markdown file ``visidata/guides/{name}.md``.
3. Write the guide.


Hello Guide
------------

This same general structure and process should work for most guides.

Step 1. Launch **GuideIndex** and find the ``name`` of the guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: ../assets/guide.png
    :width: 1000

Within VisiData, ``Space open-guide-index`` to see the Table of Contents.

``gv`` to show the **name** column. Choose a guide to work on, and note down its **name**.
For example: **MacrosSheet**.

::

Step 2. Create a markdown file ``visidata/guides/{name}.md``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we would create a ``visidata/guides/MacrosSheet.md``.

At the top of the file, optionally place template front matter, using YAML syntax:

::

    ---
    sheettype: Sheet
    ---

This front matter will override the default configuration for guides.

At the moment, the main configurable option is ``sheettype``. ``sheettype`` is a string for the type of sheet that the guide involves. VisiData uses this to auto-complete command + options patterns (see "stylings of note").

Its default value is ``Sheet`` (aka TableSheet), the base class for every table sheet.

.. note::

    The vast majority of guides will not need to set the front matter or change the default sheet type. Only set it if command + option patterns are failing to auto-complete.

    Feel free to ask us if unsure which sheet type to use.



Step 3. Write the guide
~~~~~~~~~~~~~~~~~~~~~~~

Next, fill out the text for the guide:

::

    ---
    sheettype: Sheet
    ---
    # Macros
    Macros allow you to bind a command sequence to a keystroke or longname, to replay when that
    keystroke is pressed or the command is executed by longname.

    The basic usage is:
        1. {help.commands.macro_record}
        2. Execute a series of commands.
        3. `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

    # The Macros Sheet

    - {help.commands.macro_sheet}

    - `d` (`delete-row`) to mark macros for deletion.
    - {help.commands.commit_sheet}
    - `Enter` (`open-row`) to open the macro in the current row, and view the series of commands composing it.
    '''

Some stylings of note:
**********************

- VisiData supports `basic markdown <https://www.markdownguide.org/basic-syntax/>`_
  like # Headings, \*\*bold\*\*, \*italics\*, \`code snippets\`, and \_underscore\_.

- VisiData has its `own display attribute syntax </docs/colors#attrs>`_. For e.g.:
    - ``[:onclick <url>]<text>[/]`` formats ``<text>`` into a clickable url that will open in ``$BROWSER``.
    - ``[:red on black]<sentence>[/]`` changes the colour of ``<sentence>`` to be red text
      on black background. Any color option can be used after ``:``,
      like ``[:warning]``, ``[:error]``, ``[:menu]``.
    - VisiData replaces ``{vd.options.disp_selected_note}`` with ``+``,
      the value that ``vd.options.disp_selected_note`` is set to.
      Reference any option value with ``{vd.options.optname}``. This is a great way to ensure
      that the appropriate option is displayed, even if the user changed the option value.

- List relevant commands with the general pattern ``- `<keystroke>` (`<longname>`) to <command helpstring>``.
  Follow the keystroke immediately after the bullet; do not say "Press" or "Use" within VisiData docs and helpstrings.
    - Use ``{help.commands.longname}`` to get the **GuideSheet** to replace it with the properly formatted string above.  You can write it out manually if it's clearer, but it's much preferred to change the docstring to make this pattern work.

- List relevant options with
  ``[:onclick options-sheet <option name>]`<option name>`[/] to <option helpstring> (default: <option default value>)``.
    - Similarly, use ``{help.options.option-name}`` to expand into the above, and prefer to modify the helpstring instead of writing it out manually.

- In general, do not use the second person perspective ("you", "yours") outside of tutorials.

.. autofunction:: visidata.vd.addGuide
.. autofunction:: visidata.vd.getGuide
