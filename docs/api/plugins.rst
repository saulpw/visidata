Plugins
========


Plugin file structure
----------------------

Most features can be self-contained in their own .py file, so that the feature is enabled or disabled by ``import``-ing that .py file or not.
A plugin is usually a single .py file, installed on the same computer as visidata.
`Instructions on how to install a plugin </docs/plugins/>`__

Plugins often start as a small snippet in ``.visidatarc``, and then the code is migrated to a separate file when it gets too large to share with other people via a short code snippet.
The actual code in either case should be identical.

.. note::

    To quickly install a personal plugin, place the plugin in the ``$HOME/.visidata/plugins/`` directory, and add an ``import`` statement to ``$HOME/.visidata/plugins/__init__.py``.
    At startup, VisiData will automatically import this ``plugins`` package and all the included plugins.

To publish a plugin, create a public repo with a .py file. To package it within VisiData, `open a PR on the VisiData repo <https://github.com/saulpw/visidata/pulls>`_, placing the code in the `the experimental folder <https://github.com/saulpw/visidata/tree/develop/visidata/experimental>`_.


Complete "Hello world" plugin example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

hello.py
^^^^^^^^^^^^^^^^

::

    '''This plugin adds the ``hello-world`` command to all sheets.
    Press ``0`` to show display options.disp_hello on the status line.'''

    __author__ = 'Jo Baz <jobaz@example.com>'

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world command')

    BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')

.. note::

Notes:

- There should be a searchable docstring description of the core features.
- Optionally include author metadata.
- Options at the top, commands at the bottom.
- Avoid toplevel imports of non-stdlib Python extensions.
