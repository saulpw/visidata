
## Commands

VisiData is *command-driven*, which means that it only does something when you tell it to.
It doesn't auto-save, or provide tool-tips on mouse-over, or show a paperclip asking if you need help after some amount of time.
It just sits there waiting for your next command.
You can leave it running for days, and it shouldn't consume any precious battery while idling in the background.

Commands are discrete units of behavior.
Given the same input, the same command should produce the same result (with a few obvious exceptions, like `random-rows`).

All state changes happen with a command.  Any commands that will result in different data being saved, are appended to the command log.

### Command Overview

Commands (and Keybindings) are managed in a similar way to options.
The same precedence hierarchy is used, so that commands can be created or overridden for a specific type of sheet, or even a
specific sheet itself.

There are no 'global' commands; however, since all Sheets ultimately inherit from BaseSheet, a command on BaseSheet is effectively a global command.

#### Command Context

The "execstr" is a string of Python code to `exec()` when the command is run.
`exec()` will look up symbols first in the current `sheet`, then the `vd` object, then finally the visidata module globals (see `addGlobals` and `getGlobals` below).
The `vd` and `sheet` symbols are available to specify explicitly.
So if a bare identifier (without either `vd.` or `sheet.`) is used in the execstr, first the sheet is checked, then `vd` is checked, then the globals dict is checked.

- Note: attributes on vd and sheet can only be set if object is given explicitly; e.g., instead of `cursorColIndex=2`, it must be `sheet.cursorColIndex=2`

#### LazyChainMap
The locals argument is a `LazyChainMap`, which chains multiple mappings together (each mapping is a progressive 'fallback').
The LazyChainMap can enumerate all of its keys, but does not compute any value unless the key is specifically fetched.
This is because there are a lot of entries in this mapping, some of which are expensive to compute.

- Note that sheet-specific commands trump globally set commands for keybindings.

Note: This means that using unqualified `options` in command execstr will use the sheet-specific options context for the current sheet.

### API

- `<SheetType>.addCommand(binding, longname, execstr, helpstr)`
  - binding
     - ESC/ALT
     - `^X` for Ctrl+X
     - curses keycodes/symbols.
     - to discover what to use for some unknown key, press that key in visidata and use the keystroke shown in the status bar.
     - Use 0-9, KEY_F*, ALT+ for keybinding.  But actually should not provide default at all.  Let user bind plugin commands how they want.
  - longname
     - use existing structure if possible:
        - 'addcol-' for commands that add a column;
        - 'open-' for commands that push a new sheet;
        - 'go-' for commands that move the cursor;
        - etc
- `BaseSheet.execCommand()`
- `vd.addGlobals()`
Global functions and other symbols can be added to this dict using `addGlobals()`.
- `vd.getGlobals()`
- `vd.bindkey()`
- `vd.unbindkey()`


### Examples

~~~
BaseSheet.addCommand('^D', 'scroll-halfpage-down', 'cursorDown(nScreenRows//2); sheet.topRowIndex += nScreenRows//2', 'scroll half page down')
~~~
