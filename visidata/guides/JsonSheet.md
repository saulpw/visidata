# Some special features for JSON

## Working with nested data

VisiData uses these conventions to display nested data:

- {{2}} indicates a nested object with 2 keys
- [3] indicates a nested array with 3 elements

[:note_type]Expanding[/] unpacks nested data column-wise, often useful for nested objects:

- {help.commands.expand-col}
- {help.commands.expand-col-depth}
- {help.commands.expand-cols}
- {help.commands.expand-cols-depth}

To revert earlier `expand-` operations:

- {help.commands.contract-col}
- {help.commands.contract-col-depth}
- {help.commands.contract-cols}
- {help.commands.contract-cols-depth}

[:note_type]Unfurling[/] unpacks nested data row-wise, often useful for nested arrays:

- {help.commands.unfurl-col}

Note that `unfurl-col` creates a new sheet with `_unfurled` appended to the name. There is no command to revert an unfurl; instead, quit the unfurled sheet.

For particularly deep or complex nested data, it can be helpful to open an individual cell as a new sheet:

- {help.commands.open-cell}

## Options to control JSON save behavior

- {help.options.json_indent}
- {help.options.json_sort_keys}
- {help.options.json_ensure_ascii}
