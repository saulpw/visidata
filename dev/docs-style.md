# VisiData Documentation Style Guide

VisiData supports basic markdown like # Headings, **bold**, *italics*, `code snippets`, and _underscore_.

VisiData has its own display attribute syntax. For e.g.:

    [:onclick <url>]<text>[/] formats <text> into a clickable url that will open in $BROWSER.

    [:red on black]<sentence>[/] changes the colour of <sentence> to be red text on black background. Any color option can be used after :, like [:warning], [:error], [:menu].

VisiData replaces `{vd.options.disp_selected_note}` with `+`, the value that `vd.options.disp_selected_note` is set to.
Reference any option value with `{vd.options.optname}`.
This is a great way to ensure that the appropriate option is displayed, even if the user changed the option value.

- Use `{help.commands.longname}` to put the properly formatted string (below) into the GuideSheet.
It’s much preferred to change the command helpstring itself, in order to make this pattern work, than to write it out manually.
It will look like this:

    - `<keystroke>` (`<longname>`) to <command helpstring>.

The keystroke immediately follows the bullet.  Do not say “Press” or “Use” within VisiData docs and helpstrings.

- List relevant options with the following pattern.

    - [:onclick options-sheet <option name>]`<option name>`[/] to <option helpstring> (default: <option default value>).

    - Similarly, prefer to use {help.options.option-name} to expand into the above, and prefer to modify the helpstring instead of writing it out manually.

 - Do not use the second person perspective (“you”, “yours”) outside of tutorials.

 - Do not mention "In VisiData" - we can assume that the user is in VisiData already.
 - Do not use extraneous filler words.
 - Use simpler words and grammar, using technical language accessible to ESL students.
    - Use the infinitive form of verbs.  Avoid using future and conditional tense.
    - Use active voice instead of passive voice.
 - Use established VisiData vocabulary, like "command" instead of "operation" or "action".
 - Use `[:semantic_color]` instead of hard-coded colors when possible.
 - Use `[:keystrokes]` in the guide for keystrokes, longnames, and CLI options--anything the user would actually type.  But not for output (what the user sees).
