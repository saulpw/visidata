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

### Caching Per-Row Data
When you need one cached value per row, use a `Column` with `cache=True` (or `cache='async'` for expensive I/O).  Don't build a separate dict — Column's cache is already keyed by `rowid` and integrates with the sheet lifecycle.  Example: `DirSheet` uses a hidden `Column('preview', width=0, cache=True, ...)` to cache preview sheet objects per file.

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
- When extracting a helper for a command, name it after the command's longname (e.g. `addcol-expr` -> `addcol_expr`).
- In general, keep `input*()` calls in the execstr, not inside helpers — the menu system inspects the execstr for the string 'input' to determine which commands take input.  To keep execstrs from getting too long, create another inputSomething(). Pass the input result into the helper as an argument.  Exception: when input should not be requested if some other condition fails, and that condition is too complicated for the execstr.
- A command can only call `input()` once, even with `replay=False`.
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
- Prefer `obj.options.foo = x` over `obj.options.set('foo', x, obj)` when equivalent.

## Credentials
- Environment variables only, never options: `os.environ.get('MY_API_KEY') or vd.fail('set $MY_API_KEY')`

## Row Properties
- `rows`, `selectedRows`, `someSelectedRows` (fails if none), `cursorRow`, `visibleRows`

## Cell Values
- Display (truncated): `col.getDisplayValue(row)` — for UI display
- Display (full): `col.getFullDisplayValue(row)` — for data operations (save, search, compare, edit)
- Raw typed: `col.getTypedValue(row)`

## Error Handling
- `vd.fail()` — user error. `vd.error()` — internal error. `vd.warning()`, `vd.status()`, `vd.debug()`
- `vd.exceptionCaught(e)` — log and continue (in loops/async)
- Use `wrapply(func, args)` instead of try/except when wrapping into `TypedExceptionWrapper`
- Fail fast when user-configured resources can't load — don't silently fall back.

### Error Messages

**Check these rules before writing any `vd.fail`, `vd.warning`, or `vd.status` string.**

1. **Lowercase start** — `no rows selected`, not `No rows selected`
2. **No trailing period** — `no rows selected`, not `no rows selected.`
3. **No contractions** — `cannot`, not `can't`; `did not`, not `didn't`
4. **Backticks wrap user-supplied values** — `` no column matching `{name}` ``, not single- or double-quoted `'{name}'` or bare `{name}`
5. **Backticks wrap commands/keystrokes/options** — `` use `append` instead ``, `` options.undo not enabled ``
6. **Full words** — `column` not `col`, `not implemented` not `notimpl`
7. **`no {thing}` for missing prerequisites** — `no regex`, `no rows selected`
8. **`cannot {verb}` for disallowed operations** — `cannot save multiple sheets to non-dir`
9. **Terse single fragments** — avoid multi-sentence messages; use semicolon to separate fragments. Most messages are flat declarative fragments (`no rows selected`, `cannot save`).
10. **Hide internals** — avoid Python method names, class names, type names in user-facing messages (except in error or debug); say what the user can do about it instead
11. **Consistent severity** — same concept should generally use the same function (fail or warning, not a mix)

## Documentation
- Always add `# rowdef:` comment above sheet classes
- Docstrings on classes (single-quoted) and methods
- **7-bit ASCII only** in comments, docstrings, and help strings. Use ASCII substitutes (`--` not `—`, `->` not `→`, `~=` not `≈`, `'` not `'`). Unicode in display characters, theme_options, and data is fine.

## Tests
- Use `.vdx` cmdlog tests for feature/behavior tests, not pytest. Pytest is only for unit tests of pure utility functions.
- Prefer `.vdx` over `.vd` for new golden tests.
- When adding or modifying a format saver, add `"roundtrip": "yes"|"inexact"` to `dev/formats.jsonl` and verify with `tests/test-roundtrip.sh <fmt>`.
- Include the issue number as a comment on the `def test_` line: `def test_foo(self):  # #2829`

## Deferred Sheets
- `rowid()` must use `calcValue()`, not `getValue()` — `getValue` checks deferred mods via `rowid`, causing infinite recursion.

## Postgres / psycopg2
- Only pass connection params (`host`, `port`, `user`, `password`) when they have values — omitting `host` uses Unix socket (peer auth), passing `localhost` forces TCP (password auth).

## Reference
- See `visidata/features/pypkg.py` for a complete example.
