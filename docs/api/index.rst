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

.. _hello-world:

Hello World
===========

As a simple example, this code can be placed in ``~/.visidatarc``:

::

    BaseSheet.addCommand('1', 'hello-world', 'status("Hello world!")')

This extends VisiData so that when :kbd:`1` is pressed on any sheet, the command called ``hello-world`` with the Python code ``status("Hello world!")`` is executed, and this prints the string "Hello world!" on the status bar.

----

.. toctree::
   :maxdepth: 1
   :caption: Table of contents
   :name: mastertoc

   options
   commands
   loaders
   extensible
   sheets
   columns
   data
   modify
   interface
   async
   plugins

----

Toplevel functions
===================

:: autofunction visidata.vd.view
:: autofunction visidata.vd.view_pandas
:: autofunction visidata.vd.run
