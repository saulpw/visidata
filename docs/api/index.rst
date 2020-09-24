.. VisiData documentation master file, created by
   sphinx-quickstart on Wed Sep 23 19:53:19 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================================
VisiData Plugin Authors Guide (v2.0)
=====================================

VisiData is designed to be **extensible**.
Anything that can be done with Python (which is basically everything) can be exposed in a VisiData interface with a minimal amount of code.

VisiData is also designed to be **modular**.
Many of its features can exist in isolation, and can be enabled or disabled independently, without affecting other features.
Modules should degrade or fail gracefully if they depend on another module which is not loaded.

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
--------------------------------------

This code can be placed in ``~/.visidatarc``:

::
    BaseSheet.addCommand('0', 'hello-world', 'status("Hello world!")')


This should be fairly self-explanatory: the Python code ``status("Hello world!")`` is executed when <kbd>0</kbd> is pressed.
See the sections on `Commands <>`__ and `Status <>`__.

Notes:

- Always include at least the author and version metadata elements.
- By convention most strings in vd are single-quoted; within an `execstr <>`__, inner strings are double-quoted.  This style is preferred to backslash escaping quotes: ``'foo("inner")'`` vs ``'foo(\'inner\')'``

.. toctree::
   :maxdepth: 2
   :caption: Table of contents
   :name: mastertoc
   :titlesonly:

   options
   commands
   extensible
   loaders

0. Notes
- In general, method names without underscores (usually camelCase) are public API
- method names with leading underscore are private to file.
- method names with embedded underscore are private to visidata internals.

Function signatures are do not include the leading self argument, whether vd or sheet or col or otherwise.  is listed 



1. Customizing
  - Options
  - Commands
  - Extensible

2. Loading and Saving
  - writing a loader

3. Core
  - VisiData, Sheet, Column
  - Compute
     - Cell, Value, DisplayValue
     - Types
     - Null
     - Errors
  - Expressions

4. Interface
  - Terminal
     - Colors
  - Cursor
  - Layout
  - Input/Edit
  - Status

5. User Concepts
  - Keys
  - Selection
  - Undo
  - Command Log and Replay

  - Aggregators
  - Sorting

6. Modifying Data
  - calc vs. get
  - put vs. set
  - commit

7. Plotting
  - Canvas, Graph

8. Performance
  - Async
  - Caches

9. Miscellaneous
  - fetching external resources

10. Releasing a Plugin


include options.md
include commands.md
include extensible.md
include loaders.md
include core.md
include compute.md
include expr.md
include interface.md
include data.md
include modify.md
include plot.md
include perf.md
include misc.md

