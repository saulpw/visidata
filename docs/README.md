# VisiData Documentation Index

Guide to what each file covers, so it's clear which files to update when user-facing behavior changes.

## Common mappings

- New/changed commands or keybindings → man.md, plus the relevant topic file
- New/changed options → customize.md, man.md
- New/changed file format support → formats.md
- New/changed column or row operations → columns.md, rows.md, edit.md
- New features may need a new doc file (add it to this README.md too)

## User Guides

- index.md: Getting started, links to demos and tutorials
- loading.md: Specifying source files, piping data in
- usage.md: Loading files, exiting, specifying file types
- navigate.md: Movement commands, vim-style keys, scrolling, searching
- move.md: Moving around and searching (FAQ-style)
- columns.md: Column manipulation: pin, move, hide/unhide, resize
- rows.md: Selecting, filtering, and toggling rows
- edit.md: Cell editing, bulk updates, regex substitution, expressions
- crud.md: Creating blank sheets, rows, and columns
- group.md: Grouping data, aggregators, descriptive statistics
- freq.md: Frequency tables, binning (discrete/numeric), pivot sheets
- join.md: Combining datasets via the Sheets Sheet
- graph.md: Drawing graphs, visualizing numeric variables
- graphics.md: Low-res terminal graphics, braille Unicode, Canvas classes
- colors.md: Color themes, interface color customization
- customize.md: .visidatarc, command bindings, Options Sheet, XDG support
- macros.md: Recording and replaying command sequences
- menu.md: Toplevel menubar, arrow key/hjkl navigation
- mouse.md: Mouse interaction options
- pipes.md: Using VisiData in stdin/stdout pipelines
- split.md: Split screen, viewing two sheets simultaneously
- save-restore.md: Saving and replaying sessions
- plugins.md: Installing plugins (builtin, pip, ~/.visidata/plugins/)
- shell.md: ZSH completion
- formats.md: Supported file formats, loaders/savers, dependencies
- internal_formats.md: .vd, .vdj, .vdx (command logs) and .vds (sheet state) formats
- gmail.md: Gmail access via OAuth 2.0 setup
- man.md: Quick reference / man page with full command and option listing

## Developer/Contributor Docs

- viewtsv.md: Annotated minimal 25-line VisiData app example
- test.md: Functional testing with .vd scripts
- contributing.md: Checklists for submitting loaders and plugins

## API Reference (api/)

Plugin/extension author documentation (reStructuredText, built with Sphinx).

- api/index.rst: Plugin Authors Guide overview
- api/sheets.rst: BaseSheet, openPath/openSource
- api/loaders.rst: Creating new loaders
- api/commands.rst: Command architecture, adding commands
- api/columns.rst: Column calculation engine (calcValue, getValue, etc.)
- api/plugins.rst: Plugin file structure and publishing
- api/options.rst: Creating configurable options
- api/async.rst: @asyncthread, threading, responsive UI
- api/data.rst: Selected rows API
- api/interface.rst: Drawing functions, window dimensions
- api/canvas.rst: Canvas graphics primitives
- api/extensible.rst: Extensible base class, monkey-patching

## Other Assets

- casts/: Asciinema terminal recordings embedded in various docs
- assets/: Screenshots and images (DirSheet, color options, Gmail OAuth steps, etc.)
