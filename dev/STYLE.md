# VisiData Coding Style and Guidelines

This document provides detailed coding patterns, conventions, and best practices for VisiData development.

## Naming Conventions

VisiData uses different naming conventions for different contexts:

### API Naming Patterns
- **`camelCaps`** - For "execstr" API (commands and expressions)
  - Example: `openRow()`, `cursorRow`, `selectedRows`
- **`under_score`** - For internal public API (can be used by other scripts)
  - Example: `reload_data()`, `process_results()`
- **`_preunder`** - For internal private API (should not be used outside, no API guarantee)
  - Example: `_init_columns()`, `_cache_value()`
- **`single`** - For common things usable in both execstr and internally
  - Example: `status`, `error`, `fail`, `warning`

### Method Privacy Conventions
- Methods with **leading underscore** are private to the file
- Methods with **embedded underscore** are private but available to VisiData internals
- Methods **without underscores** (usually camelCase) are public API

### Keybinding Notation
- Capital letters like `Z` mean `Shift+Z`. `gZ` means `g` then `Shift+Z`. Don't confuse `z` (lowercase prefix) with `Z` (Shift+Z command).

### String Quoting Style
- Most strings in VisiData are single-quoted
- Within an execstr, inner strings are double-quoted
- Preferred: `'foo("inner")'` over `'foo(\'inner\')'`

## Mandatory Functionality Requirements

### Global Sheets
Set global sheets on `vd` using `@VisiData.lazy_property`:
```python
@VisiData.lazy_property
def my_global_sheet(vd):
    return MySheet()
```
Otherwise they will not have full Sheet functionality from extensions.

### Global Variables and Functions
- Set other global vars on `vd` directly at module-level
- Add functions to `vd` with `@VisiData.api` or `@VisiData.property`

### Command Placement
Commands that reference a row or col should be on `Sheet` (not global or `BaseSheet`).

## Loaders vs Features

- **Loaders** (`visidata/loaders/`): Any module that defines a `vd.open_<ext>()` function. This is what makes `vd file.ext` or `vd file -f ext` work.
- **Features** (`visidata/features/`): Everything else — commands, UI enhancements, integrations that don't define an `open_` entry point.

If a module defines `open_<ext>`, it's a loader, even if it also adds commands or sheets.

## Feature File Structure

A typical feature file follows this pattern:

```python
"""
Optional module docstring explaining usage and behavior.
Can include examples, changelog, etc.
"""

from visidata import vd, BaseSheet, Sheet, Column
# Import other necessary classes

# rowdef: <description of what a row represents>
class MyCustomSheet(BaseSheet):
    'Brief description of the sheet'
    rowtype = 'items'  # plural noun describing row type
    columns = [
        Column('name', getter=lambda c,r: r.attribute),
        # More columns...
    ]
    nKeys = 1  # number of key columns

    def reload(self):
        # Load data into self.rows
        self.rows = [...]

    def openRow(self, row):
        # Define behavior when Enter is pressed on a row
        return SomeOtherSheet(...)

# Add commands
BaseSheet.addCommand('', 'command-name', 'python_code_to_execute', 'help string describing command')

# Add menu items
vd.addMenuItems('''
    Menu > Submenu > Item Name > command-name
    Another > Menu Path > command-name
''')

# Export to global namespace for use in expressions
vd.addGlobals(MyCustomSheet=MyCustomSheet)
```

## Command Patterns

```python
# Command with no keybinding ('' or None).
BaseSheet.addCommand('', 'command-name', 'code', 'help text')

# Command with keybinding
Sheet.addCommand('Ctrl+X', 'command-name', 'code', 'help text')

# Command with g prefix (global variant)
Sheet.addCommand('gEnter', 'dive-selected', 'openRows(selectedRows)', 'help')

# Command with z prefix (zoom/single variant)
Sheet.addCommand('zEnter', 'open-cell', 'vd.push(openCell(cursorCol, cursorRow))', 'help')
```

### execstr Input Limitation
An execstr can only call `input()` once per command execution, since replay provides a single input string. If a command needs multiple parameters, take them as a single input and split.

### Command Placement

- Put command on `BaseSheet` to be accessible in all contexts.
- Put command on `TableSheet` (same as Sheet, prefer TableSheet) to be accessible in all table-oriented contexts (with columns and rows and cells).
- Put command on specific sheet to be accessible only in that sheet's context.

## Adding to Global Namespace

**IMPORTANT**: Use keyword argument syntax, not dictionary syntax:

```python
# ✅ CORRECT
vd.addGlobals(PythonPackagesSheet=PythonPackagesSheet)
vd.addGlobals(MyClass=MyClass, my_function=my_function)

# ❌ WRONG - Don't use dictionary syntax
vd.addGlobals({'MyClass': MyClass})
```

## Menu Integration

```python
# Single menu item
vd.addMenuItem('Menu', 'Item Name', 'command-name')

# Multiple menu items (prefer this for multiple items)
vd.addMenuItems('''
    Menu > Submenu > Item Name > command-name
    Another > Menu > Item > another-command
''')
```

Menu paths use `>` separator. Examples:
- `System > Python > installed packages > open-python-packages`
- `File > Options > edit config file > open-config`
- `Data > Statistics > describe-sheet`

## Sheet Class Patterns

### Base Classes
- `BaseSheet` - Minimal sheet functionality
- `Sheet` - Basic sheet with rows
- `TableSheet` - Sheet with columns and rows (most common)
- `PythonSheet` - For Python object inspection
- `ColumnsSheet` - Sheet where rows are columns from another sheet

### Common Attributes
```python
class MySheet(Sheet):
    rowtype = 'items'        # Plural noun for status line
    columns = [...]          # List of Column objects
    nKeys = 1                # Number of key columns
    precious = True          # Prevent accidental quit without save
```

### Common Methods on Sheet
```python
def iterload(self):  # generator
    """Load data"""
    for row in some_func(self.source):  # source dependent on sheet; might be a path or df or other object
        yield row

def openRow(self, row):
    """Called when Enter is pressed on a row"""
    return SubSheet(...)

def openCell(self, col, row):
    """Called when zEnter is pressed"""
    return PyobjSheet(...)
```

## Column Patterns

```python
# Basic column with getter
Column('name', getter=lambda c,r: r.attribute)

# Column with getter and setter
Column('name',
       getter=lambda c,r: r.value,
       setter=lambda c,r,v: setattr(r, 'value', v))

# Column with type
Column('count', type=int, getter=lambda c,r: r.count)

# Column with width
Column('description', width=40, getter=lambda c,r: r.desc)

# AttrColumn - direct attribute access
AttrColumn('name')  # accesses row.name

# ItemColumn - item access
ItemColumn('key', 0)  # accesses row[0] or row['key']
```

**Note**: `ColumnItem` is a deprecated alias for `ItemColumn`. Always use `ItemColumn` in new code.

### Getting Cell Values

When accessing cell values in your code, choose the appropriate method:

```python
# For DISPLAY purposes (truncated if needed for screen width)
col.getDisplayValue(row)

# For PROCESSING full cell contents as text (recommended for features that analyze data)
col.format(col.getTypedValue(row))  # Gets full contents, even if truncated for display

# For getting raw typed value (to pass to other Python functions)
col.getTypedValue(row)  # Returns actual typed value (int, str, date, etc.)
```

**Rule of thumb**: Use `col.format(col.getTypedValue(row))` when you need the complete cell contents for processing (like sending to an API, saving to file, or analysis). Use `getDisplayValue()` only for display purposes.

## API Decorators

Add methods to existing classes using decorators:

```python
@Sheet.api
def my_new_method(sheet, arg):
    """Adds my_new_method to all Sheet instances"""
    # implementation

@Column.api
def my_column_method(col):
    """Adds my_column_method to all Column instances"""
    # implementation

@VisiData.api
def my_vd_method(vd):
    """Adds my_vd_method to VisiData class"""
    # implementation

@BaseSheet.api
def my_base_method(sheet):
    """Adds my_base_method to all BaseSheet instances"""
    # implementation
```

## Async Operations

Use `@asyncthread` for long-running operations:

```python
from visidata import asyncthread, Progress

@Sheet.api
@asyncthread
def long_operation(sheet):
    for item in Progress(sheet.rows, 'processing'):
        # do work
        pass
```

## Common Imports

```python
from visidata import (
    vd,                    # Global VisiData singleton
    BaseSheet,             # Base sheet class
    Sheet,                 # Basic sheet with rows
    TableSheet,            # Sheet with columns and rows
    Column,                # Column definition
    ColumnAttr,            # Column accessing row attributes
    ColumnItem,            # Column accessing row items
    Progress,              # Progress indicator
    asyncthread,           # Async decorator
)
```

## Working with Rows

### Selected Rows

Use built-in properties for working with selected rows:

```python
# CORRECT - Use someSelectedRows (built-in property)
Sheet.addCommand('', 'process-selected',
    'processRows(someSelectedRows)',
    'process selected rows or fail if none selected')

# WRONG - Don't manually check
Sheet.addCommand('', 'process-selected',
    'processRows(selectedRows or fail("no rows selected"))',
    'process selected rows')
```

**Available row properties**:
- `rows` - All rows in sheet
- `selectedRows` - Currently selected rows (may be empty list)
- `someSelectedRows` - Selected rows, or fail if none selected (unless in batch mode or option set)
- `cursorRow` - Row at cursor position
- `visibleRows` - on-screen visible rows

## API Keys and Credentials

### Security Best Practices

For external API integrations, **require credentials via environment variables only**:

```python
# CORRECT - Environment variable only
@VisiData.lazy_property
def my_api_client(vd):
    api_key = os.environ.get('MY_API_KEY') or vd.fail('set $MY_API_KEY')
    return MyAPIClient(api_key=api_key)

# WRONG - Don't create options for API keys
vd.option('my_api_key', '', 'API key')  # Don't do this
api_key = vd.options.my_api_key or vd.fail(...)  # Don't do this
```

### Option Naming

Use **module name** or abbrevation as prefix for options used exclusively by that module.

### Options Defined in Feature Files

When core code (e.g. `sheets.py`) needs to check an option defined by a feature file, use `options.get()` with a default so it works even if the feature isn't loaded.  Don't define the option in two places with different defaults.

## Best Practices

### Documentation

1. **Row Definition Comments**: Always document what a row represents
   ```python
   # rowdef: Distribution object from importlib.metadata
   class PythonPackagesSheet(PythonSheet):
   ```

2. **Docstrings**: Add docstrings to classes and methods
   ```python
   class MySheet(Sheet):
       'Sheet displaying something useful'

       def myMethod(self):
           'Does something specific'
   ```

3. **Module Docstrings**: Include usage instructions for complex features
   ```python
   """
   # Usage

   This feature does X, Y, Z...

   ## Commands

   - `command-name` - description
   """
   ```

### Code Style

1. **Command Names**: Use `kebab-case` for command names
   - `open-python-packages`
   - `select-duplicate-rows`
   - `freeze-col`

2. **Sheet Names**: Use descriptive, lowercase names with hyphens
   - `python-packages`
   - `describe_all`

3. **Column Lambdas**: Keep getters/setters simple and readable
   ```python
   # Good
   getter=lambda c,r: r.name

   # Also good for complex logic
   getter=lambda c,r: str(r._path.parent) if hasattr(r, '_path') and r._path else ''
   ```

4. **Sorting**: Sort rows in a sensible default order
   ```python
   self.rows = sorted(items, key=lambda x: x.name.lower())
   ```

### Integration

1. **Menu Placement**: Put commands in logical menu locations
   - System commands → `System` menu
   - Data operations → `Data` menu
   - Column operations → `Column` menu
   - Row operations → `Row` menu

2. **Key Bindings**: Only assign keybindings to frequently used commands
   - Leave `''` or `None` for rarely used commands
   - They can still be accessed via command palette or menu

3. **Error Handling**: Use VisiData's error handling
   ```python
   vd.fail('error message')      # Raises exception for user error, shows error
   vd.error('error message')     # Raises exception for internal error, shows error
   vd.warning('warning message') # Shows warning
   vd.status('status message')   # Shows status message
   vd.debug('status message')    # shows status message when options.debug is set (with e.g. CLI --debug)
   vd.exceptionCaught(e)         # Log exception and continue (used in loops/async)
   ```

   When a value should be a `TypedExceptionWrapper` on error but is not itself a larger error, use `wrapply` instead of `try/except`:
   ```python
   # ✅ GOOD - wrapply wraps exceptions into TypedExceptionWrapper automatically
   result = wrapply(some_func, arg1, arg2)

   # ❌ LESS GOOD - manual try/except for the same thing
   try:
       result = some_func(arg1, arg2)
   except Exception as e:
       result = TypedExceptionWrapper(None, exception=e)
   ```

4. **Fail-Fast for Required Resources**: When loading required external resources (templates, config files), fail immediately rather than falling back silently:
   ```python
   # ✅ GOOD - Fail fast if custom template can't be loaded
   if template_path:
       try:
           with open(template_path) as f:
               return f.read()
       except Exception as e:
           vd.exceptionCaught(e)  # this shows the developer a stacktrace
           vd.fail(f'Could not load template from {template_path}')
   return DEFAULT_TEMPLATE

   # ❌ LESS CLEAR - Silent fallback may hide configuration issues
   if template_path:
       try:
           with open(template_path) as f:
               return f.read()
       except Exception as e:
           vd.warning(f'Could not load template: {e}')
           return DEFAULT_TEMPLATE  # User may not notice the warning
   ```

   Use fail-fast when the user explicitly configured something (like a custom template path) but it doesn't work. This makes configuration errors obvious.

## Examples

See `visidata/features/pypkg.py` for a complete, real-world example.

## Development Workflow

1. **Create Feature File**: Add `.py` file to `visidata/features/`
2. **Test**: Run `vd` and test your feature interactively
3. **Iterate**: Modify code, restart VisiData, test again
4. **Document**: Add docstrings, usage instructions
5. **Commit**: Follow git commit conventions

## Related Files

- `visidata/pyobj.py` - Python object inspection sheets
- `visidata/sheet.py` - Core Sheet class
- `visidata/column.py` - Column definitions
- `visidata/main.py` - Application entry point

## Tests

### Prefer `.vdx` over `.vd` for new tests

New golden tests should use the `.vdx` format (one command per line) rather than the `.vd` cmdlog format (tab-separated columns). `.vdx` is much more readable and easier to write.
