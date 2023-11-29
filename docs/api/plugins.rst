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

    At startup, all .py files placed in the ``$HOME/.visidata/`` directory or Python code added to a ``~/.visidatarc`` will be auto-imported into VisiData.

To publish a plugin, create a public repo with a .py file. To package it within VisiData, `open a PR on the VisiData repo <https://github.com/saulpw/visidata/pulls>`_, placing the code in the `the experimental folder <https://github.com/saulpw/visidata/tree/develop/visidata/experimental>`_.


Complete "Hello world" plugin example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

hello.py
^^^^^^^^^^^^^^^^

::

    '''This plugin adds the ``hello-world`` command to all sheets.
    Press ``0`` to show display options.disp_hello on the status line.'''

    __author__ = 'Jo Baz <jobaz@example.com>'
    __version__ = '1.0'

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world command')

    BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')

If planning to open a PR on the VisiData repo, make sure the plugin contains:

* a ``__version__`` of the current release

.. note::

Notes:

- There should be a searchable docstring description of the core features.
- Include at least the author and version metadata elements.
- Options at the top, commands at the bottom.
- Avoid toplevel imports of non-stdlib Python extensions.
