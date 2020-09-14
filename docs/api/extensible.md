## Extensibility

One of VisiData's core design goals is *extensibility*.
The core data paradigm and command set are very useful, and moreso in combination.
Many of the features can exist in isolation, and can be enabled or disabled independently, without affecting other features.

So VisiData provides many features in a modular form.
These features can be enabled by importing the module, or disabled by not importing it.
Modules should degrade or fail gracefully if they depend on another module which has not been imported.

### class Extensible

Python classes usually declare and implement all methods and members in the class definition, which exists in a single source file.
A modular feature, otoh, is ideally contained in a separate source file by itself.
In this way, VisiData can use the Python `import` statement to enable (or remove the `import` to disable) these features without affecting other features.
Python modules loaded after startup can add or change functionality on existing classes; this is often called 'monkey-patching', and is useful for exactly this purpose of modular extensions.

The core classes in VisiData--BaseSheet, Column, and VisiData (the `vd` singleton)--inherit from the `Extensible` class, provides some helper functions and decorators to make monkey-patching easier and more consistent.

All of their subclasses are then also naturally Extensible.

`Sheet` (alias for `TableSheet`, a subclass of BaseSheet) is used in the following examples, but any other Extensible class would work similarly.


### `@VisiData.global\_api`

When a function is defined in a .py module in visidata, it is available as a bare 'global' in that module.

VisiData does an effective 'from X import *' for each plugin and modular feature, so that its
package ("global") scope gets all of the exposed symbols.
[See `getGlobals()` and `addGlobals()`]().

Everything in a .py module is exported automatically, unless there is an `__all__` with a list of the names of the functions that should be exported, and it will export only those.

Each VisiData feature and plugin should include an `__all__`, either empty or with an explicit list of function names to be available to [commands]() and [Expressions]().

## What to extend: Sheet, Column, VisiData, or globals?

Look at what the function uses.  If it uses a specific column, use `@Column.api` with `col` as the first "self" argument, and if you need access to the sheet, use `col.sheet`.  `vd` is always available as a global.

If it uses a sheet, use `@Sheet.api` with `sheet`.  Otherwise, use `@VisiData.api` with `vd`.

Classes and functions which don't use `vd` or `sheet` at all are candidates for the list of bare globals in `__all__`.

#### `@Extensible.api`

This decorator defines a member function on the specific class:

    @Sheet.api
    def foobar(sheet, ...):
        ...

Because this is a member function, the first parameter is the instance itself.
If this function were defined in the class, the first parameter would be named `self` by Python convention.
When members are defined in other files, it is better to use a specific local object name instead of `self`:

- VisiData: `vd`
- Sheet: `sheet`
- Column: `col'

    @VisiData.api
    def example1(vd, ...):

    @Column.api
    def example2(col, ...):

`Extensible.api` can be used either to add new member functions, or to override existing members.
To call the original function, use `func.__wrapped__`:

    @Sheet.api
    def addRow(sheet, row):
        # do something first
        addRow.__wrapped__(sheet, row)

#### `@Extensible.class\_api`

`@class\_api` works much like `@api`, but for class methods:

    @Sheet.class_api
    @classmethod
    def addCommand(cls, ...):

This is used internally but may not be all that useful for plugin and module authors.
Note that `@classmethod` must still be provided.
**The order of multiple decorators is crucial, and the `@Extensible.api` decorator must always goes first.**

#### `@Extensible.property`

This acts just like the `@property` decorator, if it were defined inline to the class.

#### `@Extensible.cached\_property`

This works like `@property`, except it only computes the value on first access, and then caches it for every subsequent usage.
For the VisiData singleton object (which is necessarily created before any modules are loaded), this may be necessary to avoid circular source dependencies.
Also, global sheets should be created on the VisiData object with `cached\_property`.
This allows them to take advantage of Sheet extensions that are loaded after the module.  [Because of how Python instantiates classes, extensions monkey-patched into a class are not also added to already-instantiated objects.]

For Sheet objects, this is useful to create meta-sheets (like the columns sheet), which are better created after the parent sheet's first reload, and then should be reused thereafter.

#### `Extensible.init(membername, constructor, copy=False)`

If a module wants to store some data on an Extensible class, it can add a member with a call to that class' `init()`:

    Sheet.init('foo', dict)

This monkey-patches `Sheet.__init__` to add the instance member `foo` to every Sheet on construction, and to initialize it with an empty dict.
To provide an initial non-object value:

    Sheet.init('bar', lambda: 42)

Note: This will not work with the VisiData (vd) object because it is instantiated very early.  Assign member variables directly on the vd object in the toplevel scope:

    vd.bar = []

This member can then be used like any other member of the class.

By default, when an instance of the class is copied, a member specified with this `init()` is reset to a newly constructed value (by calling the constructor again).
If `copy` is True, then a copy is made of the member for the new instance.

