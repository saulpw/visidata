# VisiData Options System

Reference for how options work in VisiData. Use this when working with options on sheets, paths, or globally.

## Overview

VisiData's options system (`visidata/settings.py`) provides hierarchical configuration that resolves through a chain of contexts, from most specific to least specific.

## Core Classes

- **`Option`** — a single option definition: name, value, helpstr, module, replayable flag
- **`SettingsMgr`** — the global registry (`vd._options`). Stores `{optname: {context_key: Option}}`
- **`OptionsObject`** — the public interface returned by `obj.options`. Wraps a SettingsMgr with a specific context object

## Declaring Options

```python
vd.option('name', default_value, 'help text')
vd.option('name', default_value, 'help text', replay=True)        # recorded in command log
vd.option('name', default_value, 'help text', sheettype=None)     # global-only, not per-sheet
```

## Resolution Chain

When you access `obj.options.foo`, the system resolves through contexts from highest to lowest precedence:

### For Sheets (`sheet.options.foo`)
1. **Sheet instance** — set on this specific sheet
2. **Sheet class hierarchy** — set on the sheet's class or any parent class (via MRO)
3. **Global** — set via .visidatarc, CLI args, or Options meta-sheet at runtime
4. **Default** — hardcoded in the `vd.option()` declaration

### For Paths (`path.options.foo`)
1. **Path instance** — set on this specific path (keyed by full path string)
2. **Path class** — set on the Path class (or S3Path, etc.)
3. **Global**
4. **Default**

## Setting Options

```python
# On a specific object
sheet.options.foo = value           # set on this sheet instance
path.options.foo = value            # set on this path instance

# On a class (affects all instances)
vd.options.set('foo', value, Sheet) # set on Sheet class

# Globally
vd.options.foo = value              # set globally (when no sheet context)
vd.options.set('foo', value, 'global')

# Check if explicitly set on an object (ignoring inheritance)
vd.options.getonly('foo', obj, default)
```

## How Objects Participate in Options

Any object can be an options context. The `SettingsMgr.objname()` method converts objects to string keys for storage:

| Object type | Key | Example |
|---|---|---|
| `str` | as-is | `'global'`, `'default'` |
| `None` | `'global'` | |
| `BaseSheet` instance | `sheet.name` | `'sample'` |
| `BaseSheet` subclass | `cls.__name__` | `'TableSheet'` |
| `os.PathLike` instance | `str(path)` | `'/home/user/data.csv'` |
| `os.PathLike` subclass | `cls.__name__` | `'Path'`, `'S3Path'` |

## Path Options

Paths get options the same way sheets do — via an `options` property that returns an `OptionsObject` bound to the path instance.

Since a sheet's source is typically a Path (`self.source`), the sheet can read path-level options:

```python
# In a sheet method or afterLoad hook:
pos = self.source.options.initial_pos    # read from the path
ft = self.source.options.filetype        # (future) read filetype from the path
```

This is useful when state needs to flow from CLI arg parsing (where the Path exists) to sheet loading (where the sheet exists but wasn't created yet at parse time).

## Key Files

- `visidata/settings.py` — SettingsMgr, OptionsObject, Option
- `visidata/basesheet.py:112-118` — sheet.options via _dualproperty
- `visidata/path.py` — path.options property
