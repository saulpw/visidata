---
eleventyNavigation:
    key: Macros
    order: 5
update: 2023-11-18
version: VisiData 3.0
---

# Macros

Macros allow you to bind a series of commands to a key and then replay those commands within a session by using that keystroke.

The basic usage is:
1. Press `m` (macro-record) to begin recording the macro.
2. Go through the commands you wish to record.
3. Then type `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

The macro will then be executed every time the provided keystroke is used. Note: the Alt+keys and the function keys are left unbound; overriding other keys may conflict with existing bindings, now or in the future.

Executing a macro will the series of commands starting on the current row and column on the current sheet.

# The Macros Sheet

Use `gm` (`open-macros-or-whatever`) to open an index existing macros.

Macros can be marked for deletion (with `d`). Changes can then be committed with `z Ctrl+S`.

`Enter` will open the macro in the current row, and you can view the series of commands composing it.

