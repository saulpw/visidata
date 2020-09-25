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


This should be fairly self-explanatory: the Python code ``status("Hello world!")`` is executed when :kbd:`0` is pressed.

Style Conventions
^^^^^^^^^^^^^^^^^^

- Method names with leading underscore are private to file.
- Method names with embedded underscore are private but available to visidata internals.
- Method names without underscores (usually camelCase) are public API.
- Most strings in vd are single-quoted; within an *execstr*, inner strings are double-quoted.  This style is preferred to backslash escaping quotes: ``'foo("inner")'`` vs ``'foo(\'inner\')'``

.. toctree::
   :maxdepth: 1
   :caption: Table of contents
   :name: mastertoc

   options
   commands
   extensible
   loaders
   core
   compute
   interface
   data
   modify
   async
   release
