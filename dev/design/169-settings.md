# 169-settings: Commands, Keybindings, and Options

## I. Layers of settings

- a. Settings are named globally uniquely.
- b. .visidatarc `options.foo = 42` overrides global default
- c. `.visidatarc` can override options explicitly for any layer by naming the associated 'object'.
- d. command-line option `--foo 42` overrides .visidatarc global at 'override' layer.
- e. User input (OptionsSheet) overrides currently at the 'override' layer.
- f. These layers may apply to any of these settings.  This is the resolution order (the first applicable layer is used):

   0. user sheet-specific override (not possible yet in interface)
   1. current sheet instance
   2. current sheet type
   3. current sheet parent types
   4. in session via meta-sheet
   5. command line (options only, applied on top of the overrides in .visidatarc)
   6. .visidatarc  (associated object is string 'override')
   7. global defaults  (associated object is string 'default')


## II. Commands/Keybindings

- a. `globalCommand(default_keybinding, longname, execstr)` adds a 'global' command that would be available if there were no sheets at all (Id7)
- b. `bindkey(keystrokes, longname)` creates global default keybinding (used when nothing else overrides it)
- c. `<Sheet>.addCommand()` (which has identical interface to a) sets the command on the sheet type (Id5) if <Sheet> is a SheetType, or on the sheet instance (Id4) if <Sheet> is an instance.
- d. `<Sheet>.bindkey()` does the same as (c) but for keybindings.
- e. `gD` to get to macros sheet to edit macro keybindings.
- f. `g^H` can add/edit keybindings for all commands on all sheets (Id1)
- g. `z^H` for list of sheet-specific commands (not global or on Sheet)
- h. Commands are identified by longname, and have a default keybinding.  Use None for no default.
- i. Command lists can be gotten by:
    - `commands`: dict of [Sheet] -> dict of [longname] -> Command for all commands for all sheets
    - `SheetType.commands` or `vs.commands`: dict of [longname] -> Command for all accessible commands on this sheet
    - `bindings` or `SheetType.bindings`, similarly
- j. `commands.show_version` or `commands[`show_version`] returns the Command in resolution order.  `bindings['^V']` returns the bound longname.

## III. Options

- a. `gO` (options-all) goes to sheet of all options at all layers for all sheet types (Id1)
- b. `O` (options-sheet) goes to sheet of all options for the current sheet
    - set 'value' to have it apply to only the current sheet
    - set 'default' to have it apply to all sheets of this type
- c. `zO` (options-specific) goes to sheet of options that are particular to this sheet (not global or on Sheet)
- d. `option(optname, default, helpstr)` adds a global option
- e. Option settings are rejected if they cannot be converted to the type of the default value.  None allows anytype.
- f. cmdlog sets options with command=`option`, input='value', row='my_option'
    - as though user had set it in Id1
    - global option values: sheet=empty
    - per-sheet-type option values: sheet=sheettype
    - per-sheet option values: sheet=sheetname
- g. Options can be set programmatically in .visidatarc or otherwise:
   - `<Sheet>.options.my_option = "value"` (same rules as IIc)
   - `options.my_option = "global default"`
   - `Canvas.options.my_option = 42`
- h. Options can be fetched in resolution order via either `options.my_option` or `options['my_option']`.
- i. Lists of options can be gotten from `Sheet.options.values()` or `options.values()`
