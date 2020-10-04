API Extensions
===============

One of VisiData's core design goals is **extensibility**.
Many of its features can exist in isolation, and can be enabled or disabled independently, without affecting other features.

So, VisiData encourages plugin authors to provide new features in a similarly modular form.
These features can be enabled by importing the module, or left disabled by not importing it.
Modules should degrade or fail gracefully if they depend on another module which is not available.

The ``Extensible`` base class
-----------------------------

Python classes usually implement all methods and members in the class definition, which exists in a single source file. A modular VisiData feature, by contrast, is self-contained within a separate source file, while providing methods on previously-defined classes.

Core functionality can be changed through 'monkey-patching', which is the ability for modules loaded after startup to add or change methods on existing classes.

To make this a bit easier, the core classes in VisiData inherit from the ``Extensible`` class, which provides some helper functions and decorators to make monkey-patching easier and more consistent.
All of their subclasses are then also naturally Extensible.

Extensible API
--------------

.. autoclass:: visidata.Extensible

.. autofunction:: visidata.Extensible.api

This decorator defines a member function on a specific class.

Because this is a member function, the first parameter is the instance itself.
If this function were defined in the class, the first parameter would be named ``self`` by Python convention.
When members are defined in other files, it is better to use a specific local object name instead of ``self``.
Use ``sheet`` for any Sheet type, ``col`` for any Column type, and ``vd`` for VisiData (which will shadow the global ``vd`` object, but as it is a singleton, they will be identical).

::

        @VisiData.api
        def vd_func(vd, ...):
            pass

        @Sheet.api
        def sheet_func(sheet, ...):
            pass

        @Column.api
        def col_func(col, ...):
            pass

``Extensible.api`` can be used either to add new member functions, or to
override existing members. To call the original function, use
``func.__wrapped__``:

::

        @Sheet.api
        def addRow(sheet, row):
            # do something first
            addRow.__wrapped__(sheet, row)

.. autofunction:: visidata.Extensible.class_api

``@class_api`` works much like ``@api``, but for class methods:

::

        @Sheet.class_api
        @classmethod
        def addCommand(cls, ...):

This method is used internally but may not be all that useful for plugin and module authors.
Note that ``@classmethod`` must still be provided, and **the order of multiple decorators is crucial**: ``@<class>.api``
must come before ``@classmethod``.

.. autofunction:: visidata.Extensible.property

This acts just like the ``@property`` decorator, if it were defined inline to the class.

.. autofunction:: visidata.Extensible.cached_property

This works like ``@property``, except it only computes the value on first access, and then caches it for every subsequent usage.

.. note::

    Because of how Python instantiates classes, extensions monkey-patched into a class are not also added to already-instantiated objects.
    So global sheets defined by a plugin should be added to the VisiData object with ``cached_property``.
    This way, they are not created until their first use, which allows them to take advantage of Sheet extensions that were loaded after the plugin.


.. autofunction:: visidata.Extensible.init

If a module wants to store some data on an Extensible class, it can add
a member with a call to that class' ``init()``:

::

    Sheet.init('foo', dict)

This monkey-patches ``Sheet.__init__`` to add the instance member
``foo`` to every Sheet on construction, and to initialize it with an
empty dict. To provide an initial non-object value:

::

    Sheet.init('bar', lambda: 42)

.. note::

    This will not work with the ``vd`` because it is instantiated very early.
    Instead, assign member variables directly on ``vd`` in the toplevel scope:

    ::

        vd.bar = []

    This member can then be used like any other member of the class.

By default, when an instance of the class is copied, a member specified with this ``init()`` is reset to a newly constructed value (by calling the constructor again).
If *copy* is ``True``, then a copy is made of the member for the new instance.

.. autofunction:: visidata.Extensible.global_api

When a function is defined in a .py module in visidata, it is available as a global function in that module.

VisiData does an effective ``from X import *`` for each plugin and modular feature, so that its package (or global) scope gets all of the exposed symbols.  See ``getGlobals()`` and ``addGlobals()`` <>`__.

Everything in a .py module is exported automatically, unless there is an ``__all__`` with a list of the names of the functions that should be exported, and it will export only those.

Each VisiData feature and plugin should include an ``__all__``, either empty or with an explicit list of function names to be available to `commands <>`__ and `Expressions <>`__.

What to extend: ``Sheet``, ``Column``, ``VisiData``, or globals?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look at what the function uses.
If it uses a specific column, use ``@Column.api`` with ``col`` as the first "self" argument, and if you need access to the sheet, use ``col.sheet``.

If the function naturally takes a sheet, use ``@Sheet.api`` with first argument of ``sheet``.

Otherwise, extend the VisiData object if neither Column nor Sheet are relevant.
``vd`` is always available as a global regardless.

Classes and functions which don't use ``vd`` or ``sheet`` at all are candidates for the list of bare globals in ``__all__``.


The ``vd`` singleton
-----------------------------

The VisiData class is a singleton object, containing all of VisiData's global functions and state for the current session.
This object should always be available as ``vd``.

Calling conventions
~~~~~~~~~~~~~~~~~~~

When calling functions on ``vd`` or ``sheet`` outside of a Command *execstr*, they should be properly qualified:

::

    @Sheet.api
    def show_hello(sheet):
        vd.status(sheet.options.disp_hello)

    BaseSheet.addCommand(None, 'show-hello', 'show_hello()')

The current **Sheet** and the **VisiData** object are both in scope for `execstrs <commands#execstr>`__, so within an *execstr*, the ``sheet.`` or ``vd.`` may be omitted, as in the hello world example:

::

    BaseSheet.addCommand(None, 'show-hello', 'status(options.disp_hello)')
