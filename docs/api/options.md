
One of VisiData's core design goals is *extensibility*.
Many of the features can exist in isolation, and can be enabled or disabled independently, without affecting other features.
So VisiData provides many features in a modular form.
These features can be enabled by importing the module, or disabled by not importing it.
Modules should degrade or fail gracefully if they depend on another module which has not been imported.

## Plugins
A plugin, then, is an optional Python module to extend or modify base VisiData's functionality.
Many features can be self-contained in their own .py file, so that the feature can be enabled or disabled by `import`ing that .py file or not.
(This is true of many core VisiData features as well.)

### Plugin file structure

A plugin is just one of these .py files, installed in `.visidata/plugins` on the local computer.
`import` statements for all enabled plugins go into `.visidata/plugins/__init__.py`.
Plugins can be installed and uninstalled in the Plugins Sheet, which manages this file.
At startup, VisiData automatically imports `plugins` (cfg).


### Complete "Hello world" plugin example

```
'''This plugin adds the `hello-world` command to all sheets, bound to '0' by default.
Pressing `0` will show "Hello world!" on the status line.'''

__author__ = 'Jo Baz <jobaz@example.com>'
__version__ = '1.0'

BaseSheet.addCommand('0', 'hello-world', 'status("Hello world!")')
```

This should be fairly self-explanatory: the Python code `status("Hello world!")` is executed when `0` is pressed.
See the sections on [Commands]() and [Status]() below.

Notes:
- Always include at least the author and version metadata elements.
- By convention most strings in vd use a single-quote; within the [execstr], inner strings must a double-quote.  (Python allows either)

### Installing plugins

[User docs: Installing a Plugin]

I often start with a snippet in .visidatarc, and then migrate the code to a plugin once it works.
[Unfortunately this means my .visidatarc is littered with the remains of many failed experiments.]
The code in either place should be identical.

## Options

Adding to the hello-world example, the text could be made configurable:
`
```
option('disp_hello', 'Hello world!', 'string to display for hello-world command')
BaseSheet.addCommand('0', 'hello-world', 'status(options.disp_hello)')
```

Now the user can override the string seen when they press `0`.  For example:

```
vd --disp-hello="¡Hola mundo!"
```

A plugin can override options too:

```
options.disp_hello = 'Bonjour monde!'
```

Notes:
- Getting the current value of an option is an expensive operation.  Factor out of high-performance loops.
- Assigning to unqualified `options` in command execstr will set the option on the current sheet only.
- Plugin options can also be overridden at the CLI (`--foo-ness`) or in visidatarc, like any other option.

#### Options Context

Options can have different values depending on the context in which they're used.
For instance, one TSV sheet might need its `delimiter` set to `|`, while another TSV sheet in the same session would need to use the default instead.
So most options are evaluated in the context of a specific sheet; in this case, TSVSheet.reload() uses `sheet.options.delimiter`.

Options can be overridden globally, or only for a specific sheet, or for a specific type of sheet.

- `options` above can be:
    - (sheet override) `sheet.options` to get or set options within the context of a specific sheet (this should be the usual case);
    - (class override) `<SheetType>.class_options` to set options for a particular subtype of BaseSheet;
    - (default) `vd.options` to get or set options "globally" with no other context.

Plugins should use the `sheet.options` form in general.

When fetching an option value, VisiData considers defaults and overrides in this order of precedence (lowest to highest):

- the default, from the option definition;
- a global override (set via the options sheet, or from the command-line with `-g`)
- the specific sheet type and its parents (must be set using class_options above; not possible using UI or CLI)
- the specific sheet itself (set using `sheet.options.foo = ` or on the CLI or on the sheet options sheet)

#### Options API

- `__getattr__` and `__setattr__` (`options.disp\_hello`)

This is the preferred style for getting or setting single option values.

- `options.get(optname[, default])`

Returns the value of the given optname option in the options context.  `default` is only returned if the option is not defined (instead of raising an Exception).

- `options.set(optname, value)`

Overrides the value for the optname in the options context.

- `options.getall('foo\_')`

Return dictionary of name:value for all options beginning with `foo\_` (with the prefix removed from the name).

The dict returned by `options('foo\_')` is designed to be used as kwargs to other loaders, so that their options can be passed through VisiData transparently.
For example, `csv.reader(fp, \*\*sheet.options('csv\_'))` will pass all csv options transparently to the builtin Python `csv` module.

- `vd.option(optname, default, helpstr, replay=False)`

Define a new option.

   - `optname`: name of option
        - All option names are in a global namespace.
        - Use '\_' for a word separator.
        - Theme option names should start with `disp\_` for a displayed string and `color\_` for a color option (see [Colors]()).
        - Otherwise, option names within a plugin should all start with the same short module abbreviation, like `mod\_`.
        - Consider whether some subset of options can be passed straight through to the underlying Python library via kwargs (maximum power with minimal effort).

   - `default`: default value of option with no other override
        - When setting the option, the type of the default is respected.  Strings and other types will be converted (`Exception` raised if conversion fails).
        - A default value of None allows any type.

   - `helpstr`: short description of option
        - shown in command list (`g Ctrl+H`)

   - `replay` (keyword arg, bool, default False) indicates if changes to the option should be stored in the command log.
        - If the option affects loading, transforming, or saving, then set `replay` to True.
        - In general, if an option affects the saved output, it should be replayed.

#### Examples

```
vd.option('mod_optname', 'default value', 'One line description of option effects', replay=True)

vd.options.color_current_row = 'red underline'     # option set globally

sheet.options.color_current_row = 'red underline'  # option set on sheet only

DirSheet.class_options.color_current_row = 'red underline'  # option set for all DirSheets

vd.options.mod_optname  # option without regard to a current sheet (global override only).

sheet.options.mod_optname  # get the option value given the context of a specific sheet
```

### See Also:

- `options-global` (`Shift+O`) for options sheet with no context.
- `options-sheet` (`z Shift+O`) for options sheet with this sheet's context.
