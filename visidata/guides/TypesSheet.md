# Types

Columns usually begin as untyped (`anytype`), but can be set to specific types.

- {help.commands.type-any}
- {help.commands.type-currency}
- {help.commands.type-date}
- {help.commands.type-float}
- {help.commands.type-int}
- {help.commands.type-len}
- {help.commands.type-string}

## Type formatting

VisiData pre-set defaults for formatting types:

- `currency` removes non-numeric characters and parses the remainder as `float`.
- `date` parses dates into date object (shown as ISO8601).
- `vlen` formats the cell value to the length of the content
- `float` uses the decimal seperator, keeping two significant digits.

Change float precision with:
- {help.commands.setcol-precision-less}
- {help.commands.setcol-precision-more}

To change the default fmtstr for a type:

- {help.options.disp_currency_fmt}
- {help.options.color_currency_neg}
- {help.options.disp_date_fmt}
- {help.options.disp_float_fmt}
- {help.options.disp_int_fmt}


## Importance of typing

Certain commands behave differently depending on how the column is typed.

Grouping by a numeric column in a Frequency table can result in numeric range binning. Grouping by a string results in categorical binning.

Un-typed columns (`anytype`) often default to `string`-like behaviour. Errors when working with numerical or datetime data is often due to values being considered as strings.

For example. [:code]addcol-expr col1+col2[/] results in a concatenation of the two columns when they are `anytype`, and addition when they are numerical.
