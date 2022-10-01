Options
========

Adding to the :ref:`hello world<hello-world>` example from the intro, the displayed text could be made configurable with an option:

::

    vd.option('disp_hello', 'Hello world!', 'string to display for hello-world command')

    BaseSheet.addCommand('1', 'hello-world', 'status(options.disp_hello)')


Now the user can set the option to modify which text is displayed during their session when they press :kbd:`1`.
For example, on the command line (note that the underscores can be converted to hyphens):

::

    vd --disp-hello="¡Hola mundo!"

The user can override it persistently for every session by adding a line to their ``.visidatarc``:

::

    options.disp_hello = 'Bonjour monde!'


Options Context
~~~~~~~~~~~~~~~

Options can have different values depending on the context in which they're used.
For instance, one TSV sheet might need its ``delimiter`` set to "``|``", while another TSV sheet in the same session might need to use the default ("``\t``", or TAB) instead.

Options can be overridden globally, or for all sheets of a specific type, or only for one specific sheet.

The options context should be referenced directly when setting:

    - ``sheet.options`` to *set* an option on a specific sheet instance (**sheet override**).
    - ``<SheetType>.options`` to *set* a option default for a particular type of Sheet (**class override**).
    - ``vd.options`` (or plain ``options``) to *set* an option globally for all sheets, except for sheets that have a sheet override (**global override**).

.. note::

    Class overrides prior to v2.10
    ------------------------------

    In VisiData v2.10 and earlier, class overrides had to be specified using ``<SheetType>.class_options``.
    In subsequent versions, ``.options`` can be used for getting and setting options at all levels.

Use ``sheet.options`` to *get* an option within the context of a specific sheet.
This is strongly preferred, so the user can override the option setting on a sheet-specific basis.
However, some options and situations are truly sheet-agnostic, and so ``vd.options`` (or plain ``options``) will *get* an option using the context of the **top sheet**.

When getting an option value, VisiData will look for a sheet override first, then class overrides next (from most specific subclass all the way up to BaseSheet), then a global override, before returning the default value from the option definition itself.

In general, plugins should use ``FooSheet.options`` to override values for the plugin-specific sheet type.

.. note::

    Performance
    ------------------

    Because it allows so much flexibility, getting option values is a comparatively slow operation.  For tight loops, save the option into a local variable in an outer block.  An option value can only change between commands anyway.

Options API
~~~~~~~~~~~~~~~

.. autofunction:: visidata.vd.options.__getattr__

``x = sheet.options.hello_world`` is the preferred style for getting a single option value.

.. autofunction:: visidata.vd.options.__setattr__

``sheet.options.hello_world = "Привет мир"`` is the preferred style for setting a single option value.

.. autofunction:: visidata.vd.options.get
.. autofunction:: visidata.vd.options.set
.. autofunction:: visidata.vd.options.unset
.. versionadded:: 2.1
.. autofunction:: visidata.vd.options.getall

The dict returned by ``options.getall('foo_')`` is designed to be used as kwargs to other loaders, so that their options can be passed through VisiData transparently.
For example, to pass all csv options through to the builtin Python ``csv`` module:

::

    csv.reader(fp, **sheet.options.getall('csv_'))

.. autofunction:: visidata.vd.option

.. note::

    If the option affects loading, transforming, or saving, then set *replay* to True.

Rules for naming options
^^^^^^^^^^^^^^^^^^^^^^^^

- Options defined within a plugin should all start with the same short module abbreviation, like "``mod_``".
- Except for theme option names, which should start with "``disp_``" for a displayed string and "``color_``" for a color option (see :ref:`Colors<colors>`).
- Use common abbreviations instead of full words.
- Use "``_``" (underscore) to separate words.
- Keep the option name length under 20 characters.  Maximum of 3 words (2 separators).

.. note::

    * Consider whether some subset of options can be passed straight through to the underlying Python library via kwargs (maximum power with minimal effort).

Option type
^^^^^^^^^^^^

When setting an option, strings and other types will be coerced to the type of the *default*.  An ``Exception`` is raised if conversion fails.  A *default* of ``None`` allows any type.

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
    DirSheet.options.color_current_row = 'reverse green'
