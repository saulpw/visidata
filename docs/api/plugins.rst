Plugins
========

`User docs: Installing a Plugin </docs/plugins/>`__

Plugin file structure
----------------------

Most features can be self-contained in their own .py file, so that the feature is enabled or disabled by ``import``-ing that .py file or not.
A plugin is usually a single .py file, installed on the same computer as visidata.
Plugins can be installed and uninstalled in the :ref:`Plugins Sheet </docs/plugins>`.

Plugins often start as a small snippet in ``.visidatarc``, and then the code is migrated to a separate file when it gets too large to share with other people via a short code snippet.
The actual code in either case should be identical.

To publish a plugin, create a public repo with a .py file, and a ``manifest.jsonl`` file with the following json fields.

- *name*: short name of the plugin (like ``vfake``).  Less than 20 characters.
- *description*: a "one line" searchable description of the core features.  Less than 1000 characters.
- *maintainer*: like ``Your Name <name@example.com>``.
- *latest_release*: date of most recent release, ISO formatted like ``2020-02-02``.
- *latest_ver*: version of most recent release, like ``v1.4``.
- *url*: link to the primary page (which may be the raw .py file itself, if it describes itself effectively).
- *visidata_ver*: version of VisiData required, like ``v2.0``.
- *pydeps*: space-separated list of PyPI dependencies (like in ``requirements.txt``).
- *vdplugindeps*: space-separated list of vd plugin dependencies.
- *sha256*: SHA256 hash of plugin .py of most recent release.

Multiple plugins can be defined in the same manifest; one line per plugin in the repository.

.. note::

    VisiData installs plugins in the ``$HOME/.visidata/plugins/`` directory.

    ``import`` statements for all enabled plugins go into ``$HOME/.visidata/plugins/__init__.py``.

    The entries in this file are maintained by the **Plugins Sheet**.  
    At startup, VisiData automatically imports this ``plugins`` package and all the included plugins.


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

manifest.jsonl
^^^^^^^^^^^^^^^^

::

    {
     "name": "helloworld",
     "description": "a configurable greeting on demand",
     "maintainer": "Vi Sidata <vd@example.com>",
     "latest_release": "2020-06-11",
     "url": "https://raw.githubusercontent.com/saulpw/visidata/387de72b369039ae864f1b84d8191d1085c2105b/plugins/hello.py",
     "latest_ver": "1.0",
     "visidata_ver": "2.0",
     "pydeps": "",
     "vdplugindeps": "",
     "sha256": "6b3baf4e1c4550947e611b9f1bdc96b7193f85048d0fc83880c4be0e7a5537d4"
    }

- Use ``sha256 hello.py`` to compute the hash.

.. note::

Notes:

- Include at least the author and version metadata elements.
- Options at the top, commands at the bottom.
- Avoid toplevel imports of non-stdlib Python extensions.
- To share with other people, add it to the `plugins.jsonl <>`__ and submit a PR to the `saulpw/visidata <>`__ Github repo.
