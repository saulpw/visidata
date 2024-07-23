# Types

Columns usually begin as untyped (`anytype`), but can be set.

- {help.commands.type-any}
- {help.commands.type-currency}
- {help.commands.type-date}
- {help.commands.type-float}
- {help.commands.type-int}
- {help.commands.type-len}
- {help.commands.type-string}

*Note*: `float` uses the decimal separator; `currency` removes non-numeric characters and parses as float; `date` parses dates into ISO8601 format; `len` formats the cell value to the length of the content.