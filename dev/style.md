# mandatory for functionality

- set global sheets on vd via `@VisiData.lazy_property`
   - otherwise they will not have full Sheet functionality from extensions
- set other global vars on vd directly at module-level
- add functions to vd with @VisiData.api or @VisiData.property

# Style Conventions

- camelCaps for "execstr" API (for commands and expressions)
- `under_score` for internal public API (can be used by other scripts)
- `_preunder` for internal private API (should not be used by outside scripts (no api guarantee))
- `single` for common things that can be used in either execstr or internally (like status and error)

- All VisiData functions in the API are available on the vd object, whose members are available in globals for execstr and internally.
- commands that reference a row or col should be on Sheet (not global or BaseSheet)


- Method names with leading underscore are private to file.
- Method names with embedded underscore are private but available to visidata internals.
- Method names without underscores (usually camelCase) are public API.
- Most strings in vd are single-quoted; within an *execstr*, inner strings are double-quoted.  This style is preferred to backslash escaping quotes: ``'foo("inner")'`` vs ``'foo(\'inner\')'``

# docs

- use "Ctrl+H" (titlecase Ctrl, plus sign, uppercase letter) instead of "^H"
- for commands, when space is not constrained, indicate the keystroke and add the longname in parens following the keystrokes.

