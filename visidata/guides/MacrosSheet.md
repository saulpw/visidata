# Macros
Macros allow you to bind a command sequence to a keystroke or longname, to replay when that keystroke is pressed or the command is executed by longname.

The basic usage is:
    1. {help.commands.macro_record}.
    2. Execute a series of commands.
    3. `m` again to complete the recording, and prompt for the keystroke or longname to bind it to.

The macro will then be executed everytime the provided keystroke or longname are used. Note: the Alt+keys and the function keys are left unbound; overriding other keys may conflict with existing bindings, now or in the future.

Executing a macro will the series of commands starting on the current row and column on the current sheet.

# The Macros Sheet

- {help.commands.macro_sheet}

- `d` (`delete-row`) to mark macros for deletion
- {help.commands.commit_sheet}
- `Enter` (`open-row`) to open the macro in the current row, and view the series of commands composing it'''
