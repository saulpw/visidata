# Using grep sheet

The grep sheet allows you to examine output of grep-like tools for line search.
The typical way to use it would be:
    grep -n pat file1 file2 |vd -f grep
You can also load from a saved file ending in .grep:
    grep -n pat file1 file2 > out.grep; vd -f grep out.grep

GrepSheet works with other grep-like searchers, like the best-in-class ripgrep:
    rg --sort path --json pat file1 file2 |vd -f grep
or git-grep:
    git grep -n class |vd -f grep

## Editing files by pressing Enter

Press `Enter` to edit a file at the line in question.

If the file path is relative to a different directory from the current
directory, use {help.options.grep_base_dir} to specify the base directory
for all relative paths.

## Options to control GrepSheet behavior

- {help.options.grep_base_dir}

## Useful shell commands

To make a ripvd command that lets you send grep output to visidata via "ripvd pattern",
add this to your .bashrc or .zshrc:
function ripvd() {
   # Run ripgrep for a pattern, and send the output to vd.
   # --sort path makes output order deterministic,
   # at the cost of making searching significantly slower.
   rg --sort path --json "$@" |vd -f grep
}


## Definition of the formats used by GrepSheet
A .grep file is a JSON lines file. It can be in two formats:
1) A simple container with three fields:
    file -  a string with the path to the file where the match was found (absolute or relative path)
    line_no - an integer with the line number in the file where the match was found,
    text - a string with the text of the line that matched.
2) ripgrep grep_printer format, described here:
ettps://docs.rs/grep-printer/latest/grep_printer/struct.JSON.html
