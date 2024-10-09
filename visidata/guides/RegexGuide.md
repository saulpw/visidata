# Matching And Transforming Strings With Regexes

Visidata has built-in support for Regular Expressions (regexes). There are many commands that enable you to search and transform your data using these patterns.


## Select Rows

- {help.commands.select-col-regex}
- {help.commands.select-cols-regex}

- {help.commands.unselect-col-regex}
- {help.commands.unselect-cols-regex}

## Search

### Column Name Search

- {help.commands.go-col-regex}

### Search Within Cells

- {help.commands.search-col}
- {help.commands.search-cols}

- {help.commands.searchr-col}
- {help.commands.searchr-cols}

- {help.commands.search-next}
- {help.commands.searchr-next}

### Search Within Key Column(s)

- {help.commands.search-keys}

This command limits searches only to the key columns

## Substitution

- {help.commands.setcol-regex-subst}
- {help.commands.setcol-regex-subst-all}

Note that after starting these command, there are three steps:
1. Enter the search regex
2. Press Tab, and enter replacement string
3. Press Enter to activate the replacement

Pressing enter after step 1 will immediately execute the replacement, REMOVING whatever was matched.

# Column Creation

- {help.commands.addcol-regex-subst}

- {help.commands.addcol-split}

Example: split directory paths  /foo/bar/baz.jpg

- {help.commands.addcol-capture}

Example: extract the values from 'key=value key2=val2' pairs



