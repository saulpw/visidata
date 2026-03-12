# VisiData Coding Style

## Naming Conventions

- **`camelCaps`** — execstr API: `openRow()`, `cursorRow`, `selectedRows`
- **`under_score`** — internal public API: `reload_data()`, `process_results()`
- **`_preunder`** — private API (no guarantee): `_init_columns()`, `_cache_value()`
- **`single`** — common things for both: `status`, `error`, `fail`, `warning`
- Leading underscore = private to file; embedded underscore = private to VisiData internals; no underscores (camelCase) = public API

### Keybinding Notation
- `Z` means Shift+Z. `gZ` means `g` then Shift+Z. Don't confuse `z` (prefix) with `Z` (Shift+Z).

### String Quoting
- Single quotes for most strings. Double quotes inside execstrs: `'foo("inner")'`

## Code Style

- **Indentation**: 4 spaces, always. Fix any mis-indented code you encounter.
- **Imports**: `vd` should be the first name in `from visidata import vd, ...`
- **Options**: Always `vd.options.foo`, never import `options` directly. This includes docstrings/comments that mention options — write `vd.options.foo` not `options.foo`.
- **Comments**: Always `# space` after the hash. Short explanatory comments go inline after the code: `if x:  # reason` not `# reason` on the line above. Section-header comments that describe a block of code stay on their own line — don't cram them inline onto long lines.
- **Issue refs**: Number first: `#2416  description`, not `description  #2416`.
- **Blank lines**: Two blank lines between every top-level def/class. Add blank lines between logical sections within functions.
- **Unicode escapes**: Uppercase hex: `'\u25E6'` not `'\u25e6'`
- **Command names**: `kebab-case` (`open-python-packages`, `freeze-col`)
- **`ColumnItem`** is deprecated — use `ItemColumn` in new code.
- **Redundant imports**: Remove inner-function imports when the module is already imported at the top of the file.

## Structure

### Global Sheets
```python
@VisiData.lazy_property
def my_global_sheet(vd):
    return MySheet()
```

### Feature File Layout
```python
"""Optional module docstring."""

from visidata import vd, BaseSheet, Sheet, Column

# rowdef: <what a row represents>
class MySheet(Sheet):
    'Brief description'
    rowtype = 'items'  # plural noun
    columns = [
        Column('name', getter=lambda c,r: r.attribute),
    ]

BaseSheet.addCommand('', 'command-name', 'code', 'help text')

vd.addMenuItems('''
    Menu > Submenu > Item Name > command-name
''')

vd.addGlobals(MySheet=MySheet)  # keyword args, not dict
```

### Loaders vs Features
- **Loaders** (`visidata/loaders/`): defines `vd.open_<ext>()`
- **Features** (`visidata/features/`): everything else

## Commands

```python
BaseSheet.addCommand('', 'command-name', 'code', 'help text')
Sheet.addCommand('gEnter', 'dive-selected', 'openRows(selectedRows)', 'help')
```

- Put on `BaseSheet` for all contexts, `TableSheet` for table contexts, specific sheet for that sheet only.
- Never reference exec locals (like `cursorRow`) inside list comprehension filters in execstrs — breaks on Python < 3.12. Extract to `@Sheet.api` method.
- An execstr can only call `input()` once (replay provides a single input string).
- `replay=False` — not added to cmdlog. `deprecated=True` — hidden from help. `testable=False` — excluded from test sweep.

## API Decorators

```python
@Sheet.api
def my_method(sheet, arg): ...

@VisiData.api
def my_vd_method(vd): ...
```

## Options

- Prefix options with module name/abbreviation when exclusive to that module.
- File properties (like `filetype`) belong on the path: `self.source.options.filetype`
- When core code checks an option from a feature file, use `options.get()` with a default.

## Credentials
- Environment variables only, never options: `os.environ.get('MY_API_KEY') or vd.fail('set $MY_API_KEY')`

## Row Properties
- `rows`, `selectedRows`, `someSelectedRows` (fails if none), `cursorRow`, `visibleRows`

## Cell Values
- Display: `col.getDisplayValue(row)`
- Processing: `col.format(col.getTypedValue(row))`
- Raw typed: `col.getTypedValue(row)`

## Error Handling
- `vd.fail()` — user error. `vd.error()` — internal error. `vd.warning()`, `vd.status()`, `vd.debug()`
- `vd.exceptionCaught(e)` — log and continue (in loops/async)
- Use `wrapply(func, args)` instead of try/except when wrapping into `TypedExceptionWrapper`
- Fail fast when user-configured resources can't load — don't silently fall back.

## Documentation
- Always add `# rowdef:` comment above sheet classes
- Docstrings on classes (single-quoted) and methods

## Tests
- Prefer `.vdx` over `.vd` for new golden tests.
- When adding or modifying a format saver, add `"roundtrip": "yes"|"inexact"` to `dev/formats.jsonl` and verify with `tests/test-roundtrip.sh <fmt>`.

## Reference
- See `visidata/features/pypkg.py` for a complete example.
