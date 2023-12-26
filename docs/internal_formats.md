---
eleventyNavigation:
    key: VisiData Internal Formats
    order: 99
---

VisiData created these formats that it uses:

- .vd, .vdj, and .vdx to save a Command Log (for macros and replays);
- .vds to save/restore the current set of data sheets and columns.

All internal formats have comments being lines starting with `#`, so they can all be scripts on unix if they are executable and the first line starts with hash-bang (`#!`).

## .vd

.vd is the original replay format: a TSV save of the Command Log (`g Shift+D`).  Deprecated in favor of .vdj.

## .vdj

.vdj is the next generation format, a JSONL of the Command Log.
This enables support for multi-input commands (where input is a dictionary) among other things.

Macros are stored in .vdj format (since 3.0).  Macros from previous versions in .vd format are still accepted.

## .vdx

.vdx is an experimental format for the Command Log which does not require a data editor to create.
Since much of the time the sheet/col/row cursor position columns are blank, only the command longname and input are necessary to execute a command.
So the .vdx format is lines of commands with the command longnamefirst, and then a space and input (if used).  Comments start with `#`.
The cursor can be moved specifically with the `col` and `row` commands.

This format is interesting for some use cases but not compelling enough to replace .vdj.
There is no current intent to replace the .vdj format with .vdx.

## .vds

.vds is a new, simple, multisheet format based on JSONL that includes some sheet metadata (mostly column definitions).
If you care only about the data and columns on the sheets, and not any provenance or exactitude or any of that stuff you get from going directly to the source, then you can save to .vds.
It should load generally to an index of the sheets, with each retaining the data and layout it was saved with, but without any history.
