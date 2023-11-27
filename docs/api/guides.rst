Guides
=======

Guides in VisiData are longer form writings on feature-sets that are readable from within VisiData.

Sometimes knowing that a command exists is not sufficient for understanding how it all ties together

The Guide Table of Contents is accessible by ``Space`` *open-guide-index*. Gray guides have not been written yet, and we really appreciate PR submissions. We also welcome proposals for guides you wish were part of the ToC, even if you had not written them.

The following document outlines the steps for adding a guide, and our writing style preferences.

The steps to add a Guide are:

1. Launch **GuideGuide** and find the ``name`` of the guide
2. ``GuideSheet`` subclass
3. Add docstring to its ``guide`` variable
4. ``vd.addGuide`` boilerplate to let VisiData know about the guide

Hello Guide
------------

Here's a step-by-line breakdown of a basic guide.
This same general structure and process should work for all guides.

Step 1. Launch **GuideGuide** and find the ``name`` of the guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Screenshot of GuideGuide in VisiData

With VisiData type ``Space`` *open-guide-index* , and you can see the Table of Contents. Any of the gray guides are unwritten.

Press ``gv`` to show the **name** column, and note down the **name** of the guide you want to document. For example: **FooGuide**.

::

Step 2. Create a GuideSheet subclass
-------------------------------

::

    class FooGuide(GuideSheet):
        guide = ''

-  The Guide should be the final class declaration in the Python file
   where the bulk of the code for that feature exists. In this case,
   we would add it to ``visidata/foobar.py``.

-  All Guides inherit from ``GuideSheet``.

.. autoclass:: visidata.GuideSheet

Step 3.Add docstring to its ``guide`` variable
----------------------------------------------

Next fill out the text for your guide in the ``guide`` variable:

::

    class FooGuideCls(GuideSheet):
        guide='''# FooGuide
    Foo is a view which displays your data as a tree. Trees differ in their branch numbers based on the [:onclick https://example.com/]branch algorithm[/].

    The basic usage is:
        1. Press `5F` (`open-foo`) to open the **FooSheet**.
        2. ???
        3. Profit.

    # The Foo Sheet

    Use `5b` (`bar-baz`) to bar baz your displayed tree.

    `Enter` to open the branch in the current row.
    '''

Some stylings of note:

- `Basic markdown <https://www.markdownguide.org/basic-syntax/`_ will work. VisiData supports '# Headings', \*\*bold\*\*, \*italics\*, \`code snippets\`, and \_underscore\_.
- VisiData has its `own display attribute syntax </docs/colors/>`_. For e.g., '[:onclick url]text[/] will format ``text`` into a clickable url that will open in ``$BROWSER``.
- For listing relevant commands, the general pattern should be 'Use \`keystroke\` (\`longname\`) to {helpstring}'.

Step 4. Let VisiData know about the guide
-----------------------------------------

At the bottom of the file, add ``vd.addGuide('GuideName', GuideCls)``.

Finishing off our example:

::
        vd.addGuide('FooGuide', FooGuideCls)

``vd.getGuide`` will now be able to locate your guide!

.. autofunction:: visidata.vd.addGuide
.. autofunction:: visidata.vd.getGuide
