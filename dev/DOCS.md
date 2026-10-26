# VisiData Documentation Style Guide

`docs/man.md` is generated from the manpage source (`visidata/man/vd.inc`) by `dev/mkman.sh`. Edit `vd.inc`, not `man.md`.

VisiData supports basic markdown like # Headings, **bold**, *italics*, `code snippets`, and _underscore_.

VisiData has its own display attribute syntax. For e.g.:

    [:onclick <url>]<text>[/] formats <text> into a clickable url that will open in $BROWSER.

    [:red on black]<sentence>[/] changes the colour of <sentence> to be red text on black background. Any color option can be used after :, like [:warning], [:error], [:menu].

VisiData replaces `{vd.options.disp_selected_note}` with `+`, the value that `vd.options.disp_selected_note` is set to.
Reference any option value with `{vd.options.optname}`.
This is a great way to ensure that the appropriate option is displayed, even if the user changed the option value.

- Use `{help.commands.longname}` to put the properly formatted string (below) into the GuideSheet.
It's much preferred to change the command helpstring itself, in order to make this pattern work, than to write it out manually.
It will look like this:

    - `<keystroke>` (`<longname>`) to <command helpstring>.

The keystroke immediately follows the bullet.  Do not say "Press" or "Use" within VisiData docs and helpstrings.

- List relevant options with the following pattern.

    - [:onclick options-sheet <option name>]`<option name>`[/] to <option helpstring> (default: <option default value>).

    - Similarly, prefer to use {help.options.option-name} to expand into the above, and prefer to modify the helpstring instead of writing it out manually.

 - Do not use the second person perspective ("you", "yours") outside of tutorials.

 - Do not mention "In VisiData" - we can assume that the user is in VisiData already.
 - Do not use extraneous filler words.
 - Use simpler words and grammar, using technical language accessible to ESL students.
    - Use the infinitive form of verbs.  Avoid using future and conditional tense.
    - Use active voice instead of passive voice.
 - Use established VisiData vocabulary, like "command" instead of "operation" or "action".
 - Use `[:semantic_color]` instead of hard-coded colors when possible.
 - Use backticks in guides for keystrokes, longnames, and CLI options--anything the user would actually type.  But not for output (what the user sees).  For the backtick key itself, write ``[:code]`[/]``, with no other backticks on that line (backticks pair across the line).
 - Keystrokes use the actual key combination the user presses: `Shift+F` not `F`, `Shift+W` not `W`.
 - Write modifier keys as `Ctrl+X`, `Alt+X`, `Shift+X` — never caret notation (`^X`).
 - Separate prefix modifiers from the base key with a space: `g Enter`, `z Shift+F`, `gz Enter`.  No space before a single-character key: `gq`, `g_`.
 - Prefix option names with `options.` in prose (e.g. `options.numeric_binning`). Not needed in option tables where the column header already says "option".
 - Match the surrounding entries' level of detail; loader reference additions usually need only a command summary.
 - Describe user-facing behavior, not implementation details. e.g. "Undoing on the frequency table also undoes on the source sheet" not "Both sheets share a single undo point".
 - Prefer lists to tables when each row works as a self-contained list item (not too many columns).
 - Use ASCII punctuation only. No em-dashes, en-dashes, smart quotes, or Unicode ellipses. Plain `-` or `:` instead.
 - Section headings are short noun phrases or bare imperatives ("Sort by one column", "Hide and Unhide columns"), not full sentences or "How to X" constructions.
 - Skip introductory paragraphs when the heading is self-explanatory. At most one short sentence of setup.
 - Describe what the command does, not what the UI looks like ("a prompt appears at the bottom of the screen" is UI narration).
 - Avoid hedging parentheticals like "(when available)", "(if possible)".

## Guides

Guides live in `visidata/guides/<Name>.md`, named from `guides_list` in `visidata/guide.py`.  [dev/guide-prompt.md](guide-prompt.md) and [dev/guide-review.md](guide-review.md) are the procedure for writing and reviewing one.

 - A guide is a quick reference for 5-15 related commands and options, not a tutorial.  Explain only what is special to VisiData; skip concepts with a thousand examples on the web (what a pivot table is, what a regex is).
 - Every sentence tells the user something that its heading and the helpstrings in its section do not.
 - Put `{help.commands.longname}` and `{help.options.name}` on their own list lines.  They expand to keystroke, longname, and the whole helpstring, which reads badly mid-sentence.  In prose, write the keystroke and longname by hand: `Shift+C` (`columns-sheet`).  An unbound command expands to `Space <longname>` on its own.
 - For a command bound only on another sheet type, name the sheet class: `{help.commands.IndexSheet.save_selected}`.  Say which sheet in the line before: "On the **Sheets Sheet**:".
 - The only front matter key is `sheettype`, set when the commands belong to a sheet type other than `Sheet`.
 - Phrase commands as "`<keystroke>` to <do something>".  No "Press", no "can be", no future or conditional.
 - Example tables: at most 40 characters wide and 8 rows tall, header underlined with dashes, no outer border.  Rendering strips leading indentation and wraps at 78 characters.  Most guides need no table.  Generate any example table from a batch run.
 - Spell CLI flags in full, with an option's spelled-out alias when it has one: `--readonly`, not `-ro`.
 - Use American spelling and the Oxford comma.
 - Refer to another guide by name in bold: "See the **MeltGuide** to unpivot."
 - Run `dev/guide-check.py <Name>` to catch unknown commands and options (which render as blank or raw `{...}`), non-ASCII, and wide tables.
