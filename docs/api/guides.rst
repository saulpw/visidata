Guides
=======

A VisiData Guide is a more verbose writeup of a particular set of features that explains how the features work together.  Guides are readable from within VisiData itself.

The Guide Index is accessible with ``Space open-guide-index``.


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

Within VisiData, ``Space open-guide-index``, and you can see the Table of Contents.

Press ``gv`` to show the **name** column, and note down the **name** of the guide you want to document. For example: **FooGuide**.

::

Step 2. Create a GuideSheet subclass
------------------------------------

::

    class FooGuideCls(GuideSheet):
        guide = ''

-  The Guide should be the final class declaration in the Python file
   where the bulk of the code for that feature exists. In this case,
   we would add it to ``visidata/foobar.py``.

-  All Guides inherit from ``GuideSheet``.

- The class name does not have to match the guide's **name**.

.. autoclass:: visidata.GuideSheet

Step 3. Add docstring to the ``guide`` variable
----------------------------------------------

Next fill out the text for your guide in the ``guide`` variable:

::

    class FooGuideCls(GuideSheet):
        guide='''# FooGuide
    Foo is a view which displays data as a foo. Foo differ in their branch numbers based on the [:onclick https://example.com/]foo-branch algorithm[/].

    The basic usage is:
        1. `Shift+X` (`open-foo`) to open the **FooSheet**.
        2. ???
        3. Profit.

    # The Foo Sheet

    - `zb` (`bar-baz`) to bar baz the displayed foo.
    - `Enter` to open the foo in the current row.
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

        vd.addGuide('FooGuide', FooGuideCls)

``vd.getGuide`` will now be able to locate the guide!

.. autofunction:: visidata.vd.addGuide
.. autofunction:: visidata.vd.getGuide
