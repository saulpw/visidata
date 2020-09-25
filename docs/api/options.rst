Options
========

Adding to the [hello world]() example, the displayed text could be made configurable with an option:

::

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world command')

    BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')


Now the user can set the option to modify which text is displayed during their session when they press :kbd:`0`.  For example, on the CLI:

::

    vd --disp-hello="¡Hola mundo!"

The user can override it for every session by setting it in their ``.visidatarc``, or another plugin could set the option itself:

::

    options.disp_hello = 'Bonjour monde!'


Options Context
~~~~~~~~~~~~~~~

Options can have different values depending on the context in which they're used.
For instance, one TSV sheet needs its ``delimiter`` set to "``|``", while another TSV sheet in the same session needs to use the default ("``\t``", or TAB) instead.

Options can be overridden globally, or for all sheets of a specific type, or only for one specific sheet.

The options contexts can be referenced directly:

    - ``sheet.options`` to get or set options within the context of a specific sheet (**sheet override**)
    - ``<SheetType>.class_options`` to set (but not get) options for a particular type of Sheet (**class override**)
    - ``vd.options`` (or plain ``options``) to set options "globally" with no other context (**default**)
         - or to *get* options in the context of the **top sheet**

When fetching an option value, VisiData will look for settings from option contexts in the above order, before returning the default value in the option definition itself.

In general, plugins should use ``sheet.options`` to get option values, and ``FooSheet.class_options`` to override values for the plugin-specific sheet type.

.. autofunction:: visidata.vd.options.__getattr__

This is the preferred style for getting a single option value.

.. autofunction:: visidata.vd.options.__setattr__

This is the preferred style for setting an option value.

.. autofunction:: visidata.vd.options.get

.. autofunction:: visidata.vd.options.set

.. autofunction:: visidata.vd.options.getall

The dict returned by ``options.getall('foo_')`` is designed to be used as kwargs to other loaders, so that their options can be passed through VisiData transparently.
For example, ``csv.reader(fp, **sheet.options.getall('csv_'))`` will pass all csv options transparently to the builtin Python ``csv`` module.

.. autofunction:: visidata.vd.option

Notes:

* All option names are in a global namespace.
* The maximum option name length should be 20.
* Use ``_`` (underscore) for a word separator.
* Theme option names should start with ``disp_`` for a displayed string and ``color_`` for a color option (see `Colors <>`__).
* Otherwise, option names within a plugin should all start with the same short module abbreviation, like "``mod_``".
* Consider whether some subset of options can be passed straight through to the underlying Python library via kwargs (maximum power with minimal effort).

* When setting the option, strings and other types will be converted to the ``default`` type.
* A default value of None allows any type. (``Exception`` is raised if conversion fails).
* If the option affects loading, transforming, or saving, then set ``replay`` to True.

Examples
~~~~~~~~~

::

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world')

    # option without regard to a current sheet (global override only)
    vd.options.disp_hello = 'こんにちは世界'

    # show the option value given the context of a specific sheet
    vd.status(sheet.options.disp_hello)

    # option set on specific sheet only
    sheet.options.color_current_row = 'bold blue'

    # option set for all DirSheets
    DirSheet.class_options.color_current_row = 'reverse green'



Performance notes
------------------

- Getting option values is a comparatively slow operation.  Factor option getting out of inner loops, and into a local variable in an outer block.  An option value can only change between commands anyway.

See Also:
----------

- ``options-global`` (``Shift+O``) for **Options Sheet** sheet with no context.
- ``options-sheet`` (``z Shift+O``) for **Options Sheet** with this sheet's context.
