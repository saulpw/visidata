# Selecting and filtering

Some commands operate only on "selected rows".  For instance, a common command to filter is {help.commands.dup_selected}.

Many g-prefixed commands are like this. For example, use {help.commands.edit_cell}, but use {help.commands.setcol_input}.  Search for "selected rows" in the [:onclick help-commands-all]commands list[/] or the [:onclick sysopen-help]manpage[/] for a full list.

Rows on the **Frequency Table** or **Pivot Table** reference a group of rows from the source sheet.  Selecting a row on those sheets also selects the referenced rows on the underlying source sheet.

Select and unselect rows with these commands:

## One row at a time

- {help.commands.select_row}
- {help.commands.unselect_row}
- {help.commands.stoggle_row}

## All rows at the same time

- {help.commands.select_rows}
- {help.commands.unselect_rows}
- {help.commands.stoggle_rows}

## By matching patterns

- {help.commands.select_col_regex}
- {help.commands.unselect_col_regex}
- {help.commands.select_cols_regex}
- {help.commands.unselect_cols_regex}

- {help.commands.select_equal_cell}
- {help.commands.select_equal_row}

## Select by Python expression

Python expressions can use a column value by the column name, if the
column name is a valid Python identifier (with only letters, digits, and underscores).

- {help.commands.select_expr}
- {help.commands.unselect_expr}

## Options

- {help.options.bulk_select_clear}
- {help.options.some_selected_rows}
