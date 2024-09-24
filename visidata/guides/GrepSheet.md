---
sheettype: GrepSheet
---

# Using grep sheet

The **GrepSheet** allows you to examine output of grep-like tools for line search.
The typical way to use it would be:
    grep -H -n pat file1 file2 | vd -f grep
You can also load from a saved file ending in .grep:
    grep -H -n pat file1 file2 > out.grep; vd -f grep out.grep

**GrepSheet** works with other grep-like searchers, like the best-in-class ripgrep:
    rg --sort path --json pat file1 file2 | vd -f grep
or git-grep:
    git grep -n class | vd -f grep

## Editing files by pressing Enter

- {help.commands.sysopen_row}

If the file path is relative to a different directory from the current
directory, use [:code]options.grep_base_dir[/] to specify the base directory
for all relative paths. `$EDITOR` is a set environment variable.

## Options to control GrepSheet behavior

- {help.options.grep_base_dir}
