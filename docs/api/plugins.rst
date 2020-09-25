Plugins
========

A VisiData plugin is just a small Python module that extends base VisiData's functionality.
Most features can be self-contained in their own .py file, so that the feature is enabled or disabled by ``import``-ing that .py file or not.

`User docs: Installing a Plugin </docs/plugins/>`__

Plugin file structure
----------------------

A plugin is usually a single .py file, installed in the ``$HOME/.visidata/plugins/`` directory on the same computer as visidata.
``import`` statements for all enabled plugins go into ``$HOME/.visidata/plugins/__init__.py``.
Plugins can be installed and uninstalled in the `Plugins Sheet <>`__, which maintains the entries in this ``__init__.py`` file.
At startup, VisiData automatically imports this ``plugins`` package.

Plugins often start as a small snippet in ``.visidatarc``, and then migrate the code to a separate file to share with other people.
The actual code in either case should be identical.

Complete "Hello world" plugin example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    '''This plugin adds the ``hello-world`` command to all sheets.
    Press ``0`` to show display options.disp_hello on the status line.'''

    __author__ = 'Jo Baz <jobaz@example.com>'
    __version__ = '1.0'

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world command')

    BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')

Notes:
- Always include at least the author and version metadata elements.
- Options at the top, commands at the bottom.
- Avoid toplevel imports of non-stdlib Python extensions.

Style Conventions
^^^^^^^^^^^^^^^^^^

- Method names with leading underscore are private to file.
- Method names with embedded underscore are private but available to visidata internals.
- Method names without underscores (usually camelCase) are public API.
- Most strings in vd are single-quoted; within an *execstr*, inner strings are double-quoted.  This style is preferred to backslash escaping quotes: ``'foo("inner")'`` vs ``'foo(\'inner\')'``
