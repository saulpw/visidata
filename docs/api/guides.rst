Guides
=======

A VisiData Guide is a more verbose writeup of a particular set of features that explains how the features work together.  Guides are readable from within VisiData itself.

The Guide Index is accessible with ``Space open-guide-index`` within VisiData or ``vd -P open-guide-index`` from the CLI.


.. note::

    Guides that have not been written yet are grayed out.  We love to get help with documentation, please get in touch if you want to write one or have other suggestions!

Here's an outline for adding a guide, with our writing style preferences:

1. Launch **GuideGuide** and find the ``name`` of the guide
2. ``GuideSheet`` subclass
3. Add docstring to its ``guide`` variable
4. ``vd.addGuide`` boilerplate to let VisiData know about the guide

Hello Guide
------------

This same general structure and process should work for most guides.

Step 1. Launch **GuideGuide** and find the ``name`` of the guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: ../assets/guide.png
    :width: 1000

Within VisiData, ``Space open-guide-index`` to see the Table of Contents.

``gv`` will show the **name** column. Choose a guide to work on, and note down its **name**. For example: **MacrosSheet**.

::

Step 2. Create a GuideSheet subclass
------------------------------------

::

    class MacrosGuide(GuideSheet):
        guide = ''

-  The Guide should be the final class declaration in the Python file
   where the bulk of the code for that feature exists. In this case,
   we would add it to ``visidata/macros.py``.

-  All Guides inherit from ``GuideSheet``.

- The class name does not have to match the guide's **name**.

.. autoclass:: visidata.GuideSheet

Step 3. Add docstring to the ``guide`` variable
----------------------------------------------

Next fill out the text for the guide in the ``guide`` variable:

::

    class MacrosGuide(GuideSheet):
        guide='''# Macros
    Macros allow you to bind a command sequence to a keystroke or longname, to replay when that keystroke is pressed or the command is executed by longname.

    The basic usage is:
        1. `m` (`macro-record`) to begin recording the macro.
        2. Execute a series of commands.
        3. `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

    # The Macros Sheet

    - `gm` (`macro-sheet`) to open an index of existing macros.

    - `d` (`delete-row`) to mark macros for deletion.
    - `z Ctrl+S` (`commit-sheet`) to then commit any changes.
    '''

Some stylings of note:

- `Basic markdown <https://www.markdownguide.org/basic-syntax/>`_ will work. VisiData supports # Headings, \*\*bold\*\*, \*italics\*, \`code snippets\`, and \_underscore\_.
- VisiData has its `own display attribute syntax </docs/colors#attrs>`_. For e.g., ``[:onclick url]text[/]`` will format ``text`` into a clickable url that will open in ``$BROWSER``. ``[:red on black]sentence[/]`` will change the colour of ``sentence`` to be red text on black background.
- For listing relevant commands, the general pattern should be ``- `keystroke` (`longname`) to {helpstring}``.  The keystroke should immediately follow the bullet; do not say "Press" or "Use" within VisiData docs and helpstrings.
- Generally, the second person perspective ("you", "yours") is not used outside of tutorials.

Step 4. Let VisiData know about the guide
-----------------------------------------

At the bottom of the file, add ``vd.addGuide('GuideName', GuideClass)``.

Finishing off our example:

::

        vd.addGuide('MacrosSheet', MacrosGuide)

``vd.getGuide`` will now be able to locate the guide!

.. autofunction:: visidata.vd.addGuide
.. autofunction:: visidata.vd.getGuide
