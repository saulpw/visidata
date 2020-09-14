
VisiData is designed to be **extensible**.
Anything that can be done with Python (which is basically everything) can be exposed in a VisiData interface with a minimal amount of code.

VisiData is also designed to be **modular**.
Many of its features can exist in isolation, and can be enabled or disabled independently, without affecting other features.
Modules should degrade or fail gracefully if they depend on another module which is not loaded.

## Plugins

A VisiData plugin is just a small Python module that extends base VisiData's functionality.
Most features can be self-contained in their own .py file, so that the feature is enabled or disabled by `import`ing that .py file or not.

### Plugin file structure

A plugin is usually a single .py file, installed in the `$HOME/.visidata/plugins/` directory on the local computer.
`import` statements for all enabled plugins go into `$HOME/.visidata/plugins/__init__.py`.
Plugins can be installed and uninstalled in the [Plugins Sheet](), which maintains the entries in this `__init__.py` file.
At startup, VisiData automatically imports this `plugins` package.

Plugins often start as a small snippet in .visidatarc, and then migrate the code to a separate file to share with other people.
The actual code in either case should be identical.

### Complete "Hello world" plugin example

To follow-along, this code can be placed in `~/.visidatarc`:

~~~
'''This plugin adds the `hello-world` command to all sheets, bound to '0' by default.
Pressing `0` will show "Hello world!" on the status line.'''

__author__ = 'Jo Baz <jobaz@example.com>'
__version__ = '1.0'

BaseSheet.addCommand('0', 'hello-world', 'status("Hello world!")')
~~~

This should be fairly self-explanatory: the Python code `status("Hello world!")` is executed when `0` is pressed.
See the sections on [Commands]() and [Status]() below.

Notes:

- Always include at least the author and version metadata elements.
- By convention most strings in vd are single-quoted; within an [execstr](), inner strings are double-quoted.  This style is preferred to backslash escaping quotes: `'foo("inner")'` vs `'foo(\'inner\')'`

### Installing plugins

[User docs: Installing a Plugin](/docs/plugins/)


## Options

Adding to the hello-world example, the text could be made configurable:

~~~
option('disp_hello', 'Hello world!', 'string to display for hello-world command')

BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')
~~~

Now the user can set the option to modify which text is displayed during their session when they press `0`.  For example, on the CLI:

~~~
vd --disp-hello="¡Hola mundo!"
~~~

The user can override it for every session by setting it in their `.visidatarc`, or another plugin could set the option itself:

~~~
options.disp_hello = 'Bonjour monde!'
~~~

#### Options Context

Options can have different values depending on the context in which they're used.
For instance, one TSV sheet needs its `delimiter` set to "`|`", while another TSV sheet in the same session needs to use the default (TAB) instead.

Options can be overridden globally, or for all sheets of a specific type, or only for one specific sheet.

- The options contexts can be referenced directly:

    - (sheet override) `sheet.options` to get or set options within the context of a specific sheet;
    - (class override) `<SheetType>.class_options` to set options for a particular type of Sheet (and all of its subclasses);
    - (default) `vd.options` to get or set options "globally" with no other context.

When fetching an option value, VisiData will look for settings from option contexts in the above order, before returning the default value in the option definition itself.

In general, plugins should use `sheet.options` to get option values, and `FooSheet.class_options` to override values for the plugin-specific sheet type.

#### Options API

- `__getattr__` and `__setattr__` (`options.disp_hello` above)

This is the preferred style for getting or setting single option values.

- `options.get(optname[, default])`

Returns the value of the given optname option in the options context.  `default` is only returned if the option is not defined (instead of raising an Exception).

- `options.set(optname, value)`

Overrides the value for the optname in the options context.

- `options.getall('foo_')`

Return dictionary of name:value for all options beginning with `foo_` (with the prefix removed from the name).

The dict returned by `options('foo_')` is designed to be used as kwargs to other loaders, so that their options can be passed through VisiData transparently.
For example, `csv.reader(fp, **sheet.options('csv_'))` will pass all csv options transparently to the builtin Python `csv` module.

- `vd.option(optname, default, helpstr, replay=False)`: Declare a new option.
   - `optname`: name of option
        - All option names are in a global namespace.
        - The maximum option name length should be 20.
        - Use "`_`" for a word separator.
        - Theme option names should start with `disp_` for a displayed string and `color_` for a color option (see [Colors]()).
        - Otherwise, option names within a plugin should all start with the same short module abbreviation, like "`mod_`".
        - Consider whether some subset of options can be passed straight through to the underlying Python library via kwargs (maximum power with minimal effort).

   - `default`: default value of option with no other override
        - When setting the option, the type of the default is respected.  Strings and other types will be converted (`Exception` raised if conversion fails).
        - A default value of None allows any type.

   - `helpstr`: short description of option
        - shown in **Options Sheet** (`Shift+O`)

   - `replay` (keyword arg, bool, default False) indicates if changes to the option should be stored in the **Command Log**.
        - If the option affects loading, transforming, or saving, then set `replay` to True.
        - In general, if an option affects the saved output, it should be replayed.

#### Examples

~~~
vd.option('mod_optname', 'default value', 'One line description of option effects', replay=True)

# option set globally
vd.options.color_current_row = 'red underline'

# option set on sheet only
sheet.options.color_current_row = 'red underline'

# option set for all DirSheets
DirSheet.class_options.color_current_row = 'red underline'

# option without regard to a current sheet (global override only)
vd.options.disp_hello = 'こんにちは世界'

# show the option value given the context of a specific sheet
vd.status(sheet.options.disp_hello)
~~~

### Performance notes

- Options are comparatively slow, so their usage should stay out of inner loops.  Factor into a local variable in an outer block.

### See Also:

- `options-global` (`Shift+O`) for **Options Sheet** sheet with no context.
- `options-sheet` (`z Shift+O`) for **Options Sheet** with this sheet's context.
